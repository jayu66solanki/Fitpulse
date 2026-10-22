# FITPULSE: WORKOUT & NUTRITION ANALYTICS ENGINE
#### Video Demo:  <URL HERE>
#### Description:

FitPulse is an interactive, terminal-based fitness and sports nutrition analytics application developed in Python. Designed for strength athletes, bodybuilders, and fitness enthusiasts, FitPulse streamlines training planning, nutrition calibration, and workout progression tracking in a unified command-line interface.

In strength training and fitness, athletes often struggle with two fundamental challenges: calculating accurate training loads and nutritional targets based on validated physiological models, and measuring whether progressive overload has truly occurred over successive training sessions. FitPulse solves both problems by bringing scientific strength formulas (Epley, Brzycki, and Lombardi), clinical metabolic expenditure equations (Mifflin-St Jeor), and quantitative volume-load progression tracking directly to the terminal.

---

### Project Architecture & File Breakdown

The project follows a modular, robust architecture structured across the following files:

1. **`project.py`**:
   The core executable of the application. It contains the primary `main()` execution loop alongside four custom top-level functions defined at global scope to satisfy the CS50P requirements:
   - `calculate_one_rep_max(weight, reps, formula)`: Computes an athlete's estimated maximum single-repetition lift (1RM) using three peer-reviewed equations. In addition to estimating 1RM, the application uses this calculation to project percentage-based training loads ranging from 100% down to 65% for powerlifting and hypertrophy programming.
   - `calculate_tdee(weight_kg, height_cm, age, gender, activity_level)`: Determines Basal Metabolic Rate (BMR) via the Mifflin-St Jeor formula and scales it against standard physical activity multipliers (sedentary, light, moderate, active, very active) to determine Total Daily Energy Expenditure (TDEE).
   - `calculate_macros(tdee, goal, weight_kg)`: Tailors daily macronutrient distributions (protein, fats, carbohydrates) based on specific caloric objectives (fat loss / cutting at a 500 kcal deficit, body recomposition / maintenance, or muscle gain / bulking at a 300 kcal surplus). It establishes protein targets at 2.0g per kilogram of bodyweight and allocates 25% of caloric intake to dietary fats before dedicating remaining calories to carbohydrates.
   - `evaluate_progressive_overload(prev_volume, current_volume)`: Quantifies session volume load ($Sets \times Reps \times Weight$) and compares current performance against previous sessions to deliver an actionable verdict (`PROGRESSION`, `MAINTAINED`, or `REGRESSION`).
   - Supporting CLI helpers: Features menu dispatchers, user input validation loops with informative error reporting, CSV read/write persistence handlers, and a dual-mode table rendering system (`render_table`) that utilizes the `tabulate` library when installed while seamlessly falling back to a clean built-in ASCII table generator if dependencies are absent.

2. **`test_project.py`**:
   The automated test suite designed for execution with `pytest`. It verifies each of the core custom functions with thorough test cases:
   - Validating identity cases (e.g., a single rep returns the exact weight lifted).
   - Testing multi-rep calculations across Epley, Brzycki, and Lombardi formulas.
   - Testing male and female BMR calculations, activity multipliers, and case-insensitive user inputs.
   - Testing caloric shifts and macronutrient balance across cutting, maintenance, and bulking regimens.
   - Testing progressive overload transitions including new baselines and percentage shifts.
   - Asserting proper `pytest.raises(ValueError)` exceptions whenever invalid inputs (non-positive numbers, negative volumes, unrecognized formulas or goals) are supplied.

3. **`requirements.txt`**:
   Specifies third-party library dependencies needed for the enhanced display and automated testing:
   - `tabulate`: Formats workout logs, training percentages, and nutrition plans into clean Unicode rounded tables.
   - `pytest`: Executes the comprehensive test suite to verify code correctness.

4. **`workouts.csv`**:
   The persistent storage file generated automatically when users log exercises. It stores historical session metrics including Exercise Name, Sets, Reps, Weight (kg), and Total Volume Load (kg).

---

### Key Design Decisions and Trade-offs

During the conception and development of FitPulse, several architectural decisions were evaluated:

- **Decoupling Pure Computational Functions from I/O**:
  A major design choice was keeping all calculation routines (`calculate_one_rep_max`, `calculate_tdee`, `calculate_macros`, `evaluate_progressive_overload`) strictly pure and decoupled from `input()` and `print()` operations. This ensures that every computational engine can be tested deterministically in `test_project.py` without requiring simulated stdin mocking, while making the functions reusable in any future interface (such as a GUI or web API).

- **Selecting the Mifflin-St Jeor Formula over Harris-Benedict**:
  While the original Harris-Benedict equation is historic, contemporary nutritional science demonstrates that the Mifflin-St Jeor equation delivers significantly more accurate estimates of BMR in modern populations (typically within a 10% margin of calorimetric measurements). FitPulse adopted Mifflin-St Jeor to ensure real-world utility for users.

- **Handling Multiple 1RM Formulas**:
  No single 1RM formula fits every repetition range equally well. Epley tends to remain accurate for moderate repetitions (3–10 reps), whereas Brzycki becomes unstable near 37 repetitions where the denominator approaches zero. To balance flexibility and mathematical safety, FitPulse supports Epley as the sensible default, provides Brzycki and Lombardi as user selections, and includes strict bounds checking to prevent division by zero or negative outputs.

- **Lightweight CSV Persistence vs. Database**:
  Rather than introducing the overhead of an external SQL database or complex ORM, FitPulse leverages Python's built-in `csv` module for workout history. This allows the application to remain self-contained, easily inspectable in spreadsheet software like Microsoft Excel or Google Sheets, and portable across platforms without additional database configuration.

---

### How to Run and Test

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**:
   ```bash
   python project.py
   ```

3. **Run Unit Tests with pytest**:
   ```bash
   pytest test_project.py
   ```

4. **Submit to CS50**:
   ```bash
   submit50 cs50/problems/2022/python/project
   ```
