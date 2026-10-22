from __future__ import annotations
import csv
import os
import sys
try:
    from tabulate import tabulate
    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False
DEFAULT_DATA_FILE = "workouts.csv"
def calculate_one_rep_max(weight: float, reps: int, formula: str = "epley") -> float:
    """
    Calculates estimated 1-Rep Max (1RM) using scientific strength formulas.

    Supported formulas:
    - 'epley': weight * (1 + reps / 30.0)
    - 'brzycki': weight * (36.0 / (37.0 - reps))
    - 'lombardi': weight * (reps ** 0.10)

    :param weight: The weight lifted (must be > 0)
    :param reps: Repetitions completed (must be >= 1)
    :param formula: Strength formula ('epley', 'brzycki', 'lombardi')
    :return: Estimated 1RM rounded to 2 decimal places
    :raises ValueError: For invalid weight, reps, or formula
    """
    if not isinstance(weight, (int, float)) or weight <= 0:
        raise ValueError("Weight must be a positive number.")
    if not isinstance(reps, int) or reps < 1:
        raise ValueError("Reps must be an integer >= 1.")

    norm_formula = formula.strip().lower()

    if reps == 1:
        return round(float(weight), 2)

    if norm_formula == "epley":
        one_rm = weight * (1.0 + reps / 30.0)
    elif norm_formula == "brzycki":
        if reps >= 37:
            raise ValueError("Brzycki formula cannot be evaluated for reps >= 37.")
        one_rm = weight * (36.0 / (37.0 - reps))
    elif norm_formula == "lombardi":
        one_rm = weight * (reps ** 0.10)
    else:
        raise ValueError(f"Unknown formula '{formula}'. Choose 'epley', 'brzycki', or 'lombardi'.")

    return round(one_rm, 2)

def calculate_tdee(weight_kg: float, height_cm: float, age: int, gender: str, activity_level: str) -> float:
    """
    Calculates Total Daily Energy Expenditure (TDEE) in calories using the Mifflin-St Jeor equation.

    Activity levels:
    - 'sedentary': 1.2
    - 'light': 1.375
    - 'moderate': 1.55
    - 'active': 1.725
    - 'very_active': 1.9

    :param weight_kg: Body weight in kilograms (must be > 0)
    :param height_cm: Height in centimeters (must be > 0)
    :param age: Age in years (must be > 0)
    :param gender: 'male' or 'female'
    :param activity_level: Activity multiplier category
    :return: Estimated TDEE calories rounded to 2 decimal places
    :raises ValueError: For invalid measurements, gender, or activity level
    """
    if not isinstance(weight_kg, (int, float)) or weight_kg <= 0:
        raise ValueError("Weight must be a positive number.")
    if not isinstance(height_cm, (int, float)) or height_cm <= 0:
        raise ValueError("Height must be a positive number.")
    if not isinstance(age, int) or age <= 0:
        raise ValueError("Age must be a positive integer.")

    norm_gender = gender.strip().lower()
    if norm_gender == "male":
        bmr = (10.0 * weight_kg) + (6.25 * height_cm) - (5.0 * age) + 5.0
    elif norm_gender == "female":
        bmr = (10.0 * weight_kg) + (6.25 * height_cm) - (5.0 * age) - 161.0
    else:
        raise ValueError("Gender must be 'male' or 'female'.")

    activity_multipliers = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9,
    }

    norm_activity = activity_level.strip().lower()
    if norm_activity not in activity_multipliers:
        raise ValueError(f"Unknown activity level '{activity_level}'. Choose from: {list(activity_multipliers.keys())}")

    tdee = bmr * activity_multipliers[norm_activity]
    return round(tdee, 2)


def calculate_macros(tdee: float, goal: str, weight_kg: float) -> dict:
    """
    Calculates daily caloric targets and macronutrient split (Protein, Fat, Carbs) based on fitness goal.

    Goals:
    - 'cut': -500 kcal deficit
    - 'maintain': 0 kcal adjustment
    - 'bulk': +300 kcal surplus

    Macronutrient distribution:
    - Protein: 2.0g per kg of bodyweight (4 kcal/g)
    - Fat: 25% of total target calories (9 kcal/g)
    - Carbs: Remainder of calories (4 kcal/g)

    :param tdee: Baseline Total Daily Energy Expenditure (must be > 0)
    :param goal: 'cut', 'maintain', or 'bulk'
    :param weight_kg: Body weight in kilograms (must be > 0)
    :return: Dict containing 'calories', 'protein_g', 'fat_g', 'carbs_g'
    :raises ValueError: For invalid TDEE, weight, or goal
    """
    if not isinstance(tdee, (int, float)) or tdee <= 0:
        raise ValueError("TDEE must be a positive number.")
    if not isinstance(weight_kg, (int, float)) or weight_kg <= 0:
        raise ValueError("Weight must be a positive number.")

    goal_adjustments = {
        "cut": -500.0,
        "maintain": 0.0,
        "bulk": 300.0,
    }

    norm_goal = goal.strip().lower()
    if norm_goal not in goal_adjustments:
        raise ValueError(f"Unknown goal '{goal}'. Choose 'cut', 'maintain', or 'bulk'.")

    target_calories = max(1000.0, tdee + goal_adjustments[norm_goal])

    protein_g = weight_kg * 2.0
    protein_cals = protein_g * 4.0

    fat_cals = target_calories * 0.25
    fat_g = fat_cals / 9.0

    remaining_cals = target_calories - (protein_cals + fat_cals)
    carbs_g = max(0.0, remaining_cals / 4.0)

    return {
        "calories": round(target_calories, 2),
        "protein_g": round(protein_g, 2),
        "fat_g": round(fat_g, 2),
        "carbs_g": round(carbs_g, 2),
    }


def evaluate_progressive_overload(prev_volume: float, current_volume: float) -> dict:
    """
    Evaluates progressive overload performance across two workout sessions based on volume load.
    Volume load = sets * reps * weight.

    Classification:
    - 'PROGRESSION': Volume increase > +2.0%
    - 'MAINTAINED': Volume within [-2.0%, +2.0%]
    - 'REGRESSION': Volume decrease < -2.0%

    :param prev_volume: Volume of previous session (must be >= 0)
    :param current_volume: Volume of current session (must be >= 0)
    :return: Dict with 'volume_diff', 'pct_change', and 'status'
    :raises ValueError: If either volume is negative
    """
    if not isinstance(prev_volume, (int, float)) or prev_volume < 0:
        raise ValueError("Previous volume must be non-negative.")
    if not isinstance(current_volume, (int, float)) or current_volume < 0:
        raise ValueError("Current volume must be non-negative.")

    volume_diff = current_volume - prev_volume

    if prev_volume == 0:
        pct_change = 100.0 if current_volume > 0 else 0.0
    else:
        pct_change = (volume_diff / prev_volume) * 100.0

    if pct_change > 2.0:
        status = "PROGRESSION"
    elif pct_change < -2.0:
        status = "REGRESSION"
    else:
        status = "MAINTAINED"

    return {
        "volume_diff": round(volume_diff, 2),
        "pct_change": round(pct_change, 2),
        "status": status,
    }

def render_table(headers: list, rows: list) -> str:
    """
    Renders tabular data using tabulate if available, or a clean fallback table.
    """
    if HAS_TABULATE:
        return tabulate(rows, headers=headers, tablefmt="rounded_grid")
    
    col_widths = [len(str(h)) for h in headers]
    for row in rows:
        for idx, val in enumerate(row):
            col_widths[idx] = max(col_widths[idx], len(str(val)))

    header_str = " | ".join(str(h).ljust(col_widths[i]) for i, h in enumerate(headers))
    separator_str = "-+-".join("-" * col_widths[i] for i in range(len(headers)))
    row_strings = [
        " | ".join(str(val).ljust(col_widths[i]) for i, val in enumerate(row))
        for row in rows
    ]
    return f"{header_str}\n{separator_str}\n" + "\n".join(row_strings)


def get_training_percentages(one_rm: float) -> list:
    """
    Generates percentage-based training weight guidelines from a 1RM.
    """
    percentages = [
        (100, 1),
        (95, 2),
        (90, 3),
        (85, 5),
        (80, 8),
        (75, 10),
        (70, 12),
        (65, 15),
    ]
    table_data = []
    for pct, reps in percentages:
        load = round((pct / 100.0) * one_rm, 2)
        table_data.append([f"{pct}%", f"{load} kg", f"~{reps} reps"])
    return table_data


def save_workout(exercise: str, sets: int, reps: int, weight: float, volume: float, filepath: str = DEFAULT_DATA_FILE):
    """
    Appends a workout entry to a CSV file.
    """
    file_exists = os.path.isfile(filepath)
    with open(filepath, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Exercise", "Sets", "Reps", "Weight_kg", "Volume_kg"])
        writer.writerow([exercise.strip().title(), sets, reps, weight, volume])


def load_workouts(filepath: str = DEFAULT_DATA_FILE) -> list:
    """
    Loads all recorded workout entries from the CSV file.
    """
    if not os.path.isfile(filepath):
        return []
    workouts = []
    with open(filepath, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            workouts.append({
                "Exercise": row["Exercise"],
                "Sets": int(row["Sets"]),
                "Reps": int(row["Reps"]),
                "Weight_kg": float(row["Weight_kg"]),
                "Volume_kg": float(row["Volume_kg"]),
            })
    return workouts


def get_last_workout_volume(exercise: str, filepath: str = DEFAULT_DATA_FILE) -> float | None:
    """
    Finds the most recent volume recorded for a specific exercise.
    """
    workouts = load_workouts(filepath)
    norm_target = exercise.strip().lower()
    for entry in reversed(workouts):
        if entry["Exercise"].strip().lower() == norm_target:
            return entry["Volume_kg"]
    return None

def handle_one_rep_max_menu():
    print("\n--- 1-Rep Max (1RM) Calculator ---")
    try:
        weight = float(input("Enter weight lifted (kg/lbs): ").strip())
        reps = int(input("Enter repetitions completed: ").strip())
        print("Formulas: [1] Epley (Default)  [2] Brzycki  [3] Lombardi")
        f_choice = input("Select formula [1/2/3, Enter for 1]: ").strip()

        formula_map = {"1": "epley", "2": "brzycki", "3": "lombardi", "": "epley"}
        formula = formula_map.get(f_choice, "epley")

        one_rm = calculate_one_rep_max(weight, reps, formula=formula)
        print(f"\n>> Estimated 1RM ({formula.title()} Formula): {one_rm:.2f}")

        print("\nTraining Load Breakdown:")
        pct_table = get_training_percentages(one_rm)
        print(render_table(["Percentage", "Load", "Target Reps"], pct_table))
    except ValueError as e:
        print(f"Error: {e}")


def handle_nutrition_menu():
    print("\n--- BMR, TDEE & Macronutrient Calculator ---")
    try:
        weight = float(input("Enter body weight (kg): ").strip())
        height = float(input("Enter height (cm): ").strip())
        age = int(input("Enter age (years): ").strip())
        gender = input("Enter gender (male/female): ").strip()

        print("\nActivity Levels:")
        print("  1. Sedentary (office job, little/no exercise)")
        print("  2. Light (exercise 1-3 days/week)")
        print("  3. Moderate (exercise 3-5 days/week)")
        print("  4. Active (hard exercise 6-7 days/week)")
        print("  5. Very Active (heavy physical work or 2x/day training)")
        act_choice = input("Select activity level [1-5]: ").strip()
        act_map = {
            "1": "sedentary",
            "2": "light",
            "3": "moderate",
            "4": "active",
            "5": "very_active",
        }
        activity = act_map.get(act_choice, "sedentary")

        tdee = calculate_tdee(weight, height, age, gender, activity)
        print(f"\n>> Daily Energy Expenditure (TDEE): {tdee:.2f} kcal/day")

        print("\nFitness Goal:")
        print("  1. Cut (Fat Loss, -500 kcal)")
        print("  2. Maintain (Body Recomposition)")
        print("  3. Bulk (Muscle Gain, +300 kcal)")
        goal_choice = input("Select goal [1/2/3]: ").strip()
        goal_map = {"1": "cut", "2": "maintain", "3": "bulk"}
        goal = goal_map.get(goal_choice, "maintain")

        macros = calculate_macros(tdee, goal, weight)
        headers = ["Target Calories", "Protein (g)", "Fats (g)", "Carbs (g)"]
        rows = [[
            f"{macros['calories']} kcal",
            f"{macros['protein_g']} g ({macros['protein_g']*4:.0f} kcal)",
            f"{macros['fat_g']} g ({macros['fat_g']*9:.0f} kcal)",
            f"{macros['carbs_g']} g ({macros['carbs_g']*4:.0f} kcal)",
        ]]
        print(f"\nNutrition Targets for '{goal.upper()}':")
        print(render_table(headers, rows))
    except ValueError as e:
        print(f"Error: {e}")


def handle_workout_logger_menu():
    print("\n--- Workout Logger & Progressive Overload Evaluator ---")
    try:
        exercise = input("Enter exercise name (e.g. Barbell Squat): ").strip()
        if not exercise:
            print("Exercise name cannot be empty.")
            return

        sets = int(input("Enter number of sets: ").strip())
        reps = int(input("Enter repetitions per set: ").strip())
        weight = float(input("Enter weight lifted per set (kg): ").strip())

        if sets <= 0 or reps <= 0 or weight < 0:
            print("Sets and reps must be positive, weight non-negative.")
            return

        current_volume = sets * reps * weight
        print(f"\nCurrent Session Volume: {current_volume:.2f} kg ({sets} x {reps} @ {weight}kg)")

        prev_volume = get_last_workout_volume(exercise)
        if prev_volume is not None:
            comparison = evaluate_progressive_overload(prev_volume, current_volume)
            status_labels = {
                "PROGRESSION": "UP (+)",
                "MAINTAINED": "EVEN (=)",
                "REGRESSION": "DOWN (-)",
            }
            label = status_labels.get(comparison["status"], comparison["status"])
            print(f"Previous Session Volume: {prev_volume:.2f} kg")
            print(f"Volume Difference: {comparison['volume_diff']:+.2f} kg ({comparison['pct_change']:+.2f}%)")
            print(f">> Performance Verdict: [{label}] {comparison['status']}")
        else:
            print("No previous session found for this exercise. Setting baseline!")

        save = input("\nSave this workout to log? (y/n): ").strip().lower()
        if save in ("y", "yes"):
            save_workout(exercise, sets, reps, weight, current_volume)
            print("Workout logged successfully!")
    except ValueError as e:
        print(f"Error: {e}")


def handle_history_menu():
    print("\n--- Workout History ---")
    workouts = load_workouts()
    if not workouts:
        print("No workouts recorded yet. Start logging from option 3!")
        return

    headers = ["Exercise", "Sets", "Reps", "Weight (kg)", "Volume (kg)"]
    rows = [
        [w["Exercise"], w["Sets"], w["Reps"], f"{w['Weight_kg']:.2f}", f"{w['Volume_kg']:.2f}"]
        for w in workouts
    ]
    print(render_table(headers, rows))

def main():
    """
    Main application loop for FitPulse CLI.
    """
    banner = """
======================================================
  FITPULSE: Workout & Nutrition Analytics Engine
======================================================
"""
    print(banner)

    menu_options = {
        "1": ("Calculate 1-Rep Max & Training Percentages", handle_one_rep_max_menu),
        "2": ("Calculate BMR, TDEE & Nutrition Macros", handle_nutrition_menu),
        "3": ("Log Workout & Evaluate Progressive Overload", handle_workout_logger_menu),
        "4": ("View Workout History", handle_history_menu),
        "5": ("Exit", None),
    }

    while True:
        print("\nMain Menu:")
        for key, (desc, _) in menu_options.items():
            print(f"  [{key}] {desc}")

        choice = input("\nEnter choice [1-5]: ").strip()

        if choice == "5":
            print("\nThank you for training with FitPulse. Stay consistent!\n")
            sys.exit(0)
        elif choice in menu_options:
            handler = menu_options[choice][1]
            if handler:
                handler()
        else:
            print("Invalid selection. Please choose an option from 1 to 5.")


if __name__ == "__main__":
    main()
