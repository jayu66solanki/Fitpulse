"""
Unit tests for FitPulse (CS50's Introduction to Programming with Python - Final Project)
Executable with pytest:
    pytest test_project.py
"""

import pytest
from project import (
    calculate_one_rep_max,
    calculate_tdee,
    calculate_macros,
    evaluate_progressive_overload,
)


# ==============================================================================
# TESTS FOR calculate_one_rep_max
# ==============================================================================

def test_calculate_one_rep_max():
    # 1 rep should always equal the exact weight lifted regardless of formula
    assert calculate_one_rep_max(100.0, 1) == 100.0
    assert calculate_one_rep_max(80.5, 1, "brzycki") == 80.5
    assert calculate_one_rep_max(120, 1, "lombardi") == 120.0

    # Test default formula (Epley): weight * (1 + reps / 30)
    # 100 * (1 + 10/30) = 133.333... -> 133.33
    assert calculate_one_rep_max(100.0, 10) == 133.33
    assert calculate_one_rep_max(100.0, 10, "epley") == 133.33
    # 60 * (1 + 5/30) = 70.0
    assert calculate_one_rep_max(60.0, 5, "EPLEY") == 70.0

    # Test Brzycki formula: weight * (36 / (37 - reps))
    # 100 * (36 / (37 - 5)) = 100 * 36 / 32 = 112.50
    assert calculate_one_rep_max(100.0, 5, "brzycki") == 112.50

    # Test Lombardi formula: weight * reps ** 0.10
    # 100 * 10 ** 0.10 = 100 * 1.2589254... = 125.89
    assert calculate_one_rep_max(100.0, 10, "lombardi") == 125.89

    # Error handling tests
    with pytest.raises(ValueError):
        calculate_one_rep_max(0, 5)

    with pytest.raises(ValueError):
        calculate_one_rep_max(-50, 5)

    with pytest.raises(ValueError):
        calculate_one_rep_max(100, 0)

    with pytest.raises(ValueError):
        calculate_one_rep_max(100, -2)

    with pytest.raises(ValueError):
        calculate_one_rep_max(100, 5, "unknown_formula")

    # Brzycki cannot accept reps >= 37
    with pytest.raises(ValueError):
        calculate_one_rep_max(100, 37, "brzycki")


# ==============================================================================
# TESTS FOR calculate_tdee
# ==============================================================================

def test_calculate_tdee():
    # Male test:
    # weight=80, height=180, age=25
    # BMR = 10*80 + 6.25*180 - 5*25 + 5 = 800 + 1125 - 125 + 5 = 1805.0
    # Sedentary (* 1.2) = 2166.0
    assert calculate_tdee(80, 180, 25, "male", "sedentary") == 2166.0

    # Case insensitivity & Moderate (* 1.55) = 1805 * 1.55 = 2797.75
    assert calculate_tdee(80, 180, 25, "MALE", "MODERATE") == 2797.75

    # Female test:
    # weight=60, height=165, age=30
    # BMR = 10*60 + 6.25*165 - 5*30 - 161 = 600 + 1031.25 - 150 - 161 = 1320.25
    # Light (* 1.375) = 1320.25 * 1.375 = 1815.34375 -> 1815.34
    assert calculate_tdee(60, 165, 30, "female", "light") == 1815.34

    # Active (* 1.725) and Very Active (* 1.9)
    assert calculate_tdee(80, 180, 25, "male", "active") == round(1805.0 * 1.725, 2)
    assert calculate_tdee(80, 180, 25, "male", "very_active") == round(1805.0 * 1.9, 2)

    # Error handling tests
    with pytest.raises(ValueError):
        calculate_tdee(-70, 175, 25, "male", "sedentary")

    with pytest.raises(ValueError):
        calculate_tdee(70, -175, 25, "male", "sedentary")

    with pytest.raises(ValueError):
        calculate_tdee(70, 175, -25, "male", "sedentary")

    with pytest.raises(ValueError):
        calculate_tdee(70, 175, 25, "alien", "sedentary")

    with pytest.raises(ValueError):
        calculate_tdee(70, 175, 25, "male", "couch_potato")


# ==============================================================================
# TESTS FOR calculate_macros
# ==============================================================================

def test_calculate_macros():
    # Maintenance test (tdee=2500, weight=80)
    # Target cals: 2500
    # Protein: 80 * 2 = 160g (640 kcal)
    # Fat: 25% of 2500 = 625 kcal / 9 = 69.444... -> 69.44g
    # Carbs: (2500 - 640 - 625) / 4 = 1235 / 4 = 308.75g
    m_maintain = calculate_macros(2500.0, "maintain", 80.0)
    assert m_maintain["calories"] == 2500.0
    assert m_maintain["protein_g"] == 160.0
    assert m_maintain["fat_g"] == 69.44
    assert m_maintain["carbs_g"] == 308.75

    # Cut test (-500 kcal) -> 2000 kcal
    # Protein: 160g (640 kcal)
    # Fat: 2000 * 0.25 / 9 = 500 / 9 = 55.555... -> 55.56g
    # Carbs: (2000 - 640 - 500) / 4 = 860 / 4 = 215.0g
    m_cut = calculate_macros(2500.0, "cut", 80.0)
    assert m_cut["calories"] == 2000.0
    assert m_cut["protein_g"] == 160.0
    assert m_cut["fat_g"] == 55.56
    assert m_cut["carbs_g"] == 215.0

    # Bulk test (+300 kcal) -> 2800 kcal
    m_bulk = calculate_macros(2500.0, "bulk", 80.0)
    assert m_bulk["calories"] == 2800.0
    assert m_bulk["protein_g"] == 160.0

    # Error handling tests
    with pytest.raises(ValueError):
        calculate_macros(0, "maintain", 70)

    with pytest.raises(ValueError):
        calculate_macros(2000, "maintain", -70)

    with pytest.raises(ValueError):
        calculate_macros(2000, "lean_bulk", 70)


# ==============================================================================
# TESTS FOR evaluate_progressive_overload
# ==============================================================================

def test_evaluate_progressive_overload():
    # Progression: previous 1000, current 1100 (+10%)
    res_prog = evaluate_progressive_overload(1000.0, 1100.0)
    assert res_prog["volume_diff"] == 100.0
    assert res_prog["pct_change"] == 10.0
    assert res_prog["status"] == "PROGRESSION"

    # Maintained: previous 1000, current 1010 (+1.0%, within +/- 2%)
    res_maint = evaluate_progressive_overload(1000.0, 1010.0)
    assert res_maint["volume_diff"] == 10.0
    assert res_maint["pct_change"] == 1.0
    assert res_maint["status"] == "MAINTAINED"

    # Regression: previous 1000, current 900 (-10%)
    res_reg = evaluate_progressive_overload(1000.0, 900.0)
    assert res_reg["volume_diff"] == -100.0
    assert res_reg["pct_change"] == -10.0
    assert res_reg["status"] == "REGRESSION"

    # Edge cases: 0 previous volume
    res_first = evaluate_progressive_overload(0.0, 500.0)
    assert res_first["volume_diff"] == 500.0
    assert res_first["pct_change"] == 100.0
    assert res_first["status"] == "PROGRESSION"

    res_zero = evaluate_progressive_overload(0.0, 0.0)
    assert res_zero["status"] == "MAINTAINED"

    # Negative volume error handling
    with pytest.raises(ValueError):
        evaluate_progressive_overload(-100.0, 500.0)

    with pytest.raises(ValueError):
        evaluate_progressive_overload(500.0, -50.0)
