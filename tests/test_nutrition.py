from nutrition import log_meal, daily_calorie_summary


def test_daily_calorie_summary():
    meals = []
    user_id = "u1"

    log_meal(meals, {
        "user_id": user_id,
        "timestamp": "2025-01-01 08:00",
        "meal_type": "breakfast",
        "items": [{"name": "Oats", "grams": 80}],
        "calories": 300,
        "macros": {"protein_g": 10, "carbs_g": 50, "fat_g": 5},
    })

    log_meal(meals, {
        "user_id": user_id,
        "timestamp": "2025-01-01 13:00",
        "meal_type": "lunch",
        "items": [{"name": "Chicken", "grams": 200}],
        "calories": 600,
        "macros": {"protein_g": 45, "carbs_g": 10, "fat_g": 20},
    })

    s = daily_calorie_summary(meals, user_id, "2025-01-01")
    assert s["total_calories"] == 900.0
    assert s["by_meal_type"]["breakfast"] == 300.0
    assert s["by_meal_type"]["lunch"] == 600.0
