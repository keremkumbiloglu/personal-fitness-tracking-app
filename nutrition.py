from __future__ import annotations

import uuid
from datetime import datetime


def log_meal(meals: list, meal_data: dict) -> dict:
    meal = dict(meal_data)
    meal["id"] = meal.get("id") or str(uuid.uuid4())
    meal.setdefault("allow_future", False)
    meals.append(meal)
    return meal


def update_meal(meals: list, meal_id: str, updates: dict) -> dict:
    m = next((x for x in meals if x.get("id") == meal_id), None)
    if not m:
        raise ValueError("Meal not found.")
    m.update(updates)
    return m


def delete_meal(meals: list, meal_id: str) -> bool:
    idx = next((i for i, x in enumerate(meals) if x.get("id") == meal_id), None)
    if idx is None:
        return False
    meals.pop(idx)
    return True


def daily_calorie_summary(meals: list, user_id: str, date: str) -> dict:
    total = 0.0
    by_type = {"breakfast": 0.0, "lunch": 0.0, "dinner": 0.0, "snack": 0.0}

    for m in meals:
        if m.get("user_id") != user_id:
            continue
        ts = m.get("timestamp", "")
        if ts.startswith(date):
            cals = float(m.get("calories", 0))
            total += cals
            mt = m.get("meal_type")
            if mt in by_type:
                by_type[mt] += cals

    return {"date": date, "total_calories": round(total, 1), "by_meal_type": {k: round(v, 1) for k, v in by_type.items()}}


def macro_breakdown(meals: list, user_id: str, date_range: tuple[str, str]) -> dict:
    start, end = date_range
    start_d = datetime.strptime(start, "%Y-%m-%d").date()
    end_d = datetime.strptime(end, "%Y-%m-%d").date()

    protein = carbs = fat = calories = 0.0

    for m in meals:
        if m.get("user_id") != user_id:
            continue
        ts = m.get("timestamp", "")
        try:
            d = datetime.strptime(ts, "%Y-%m-%d %H:%M").date()
        except Exception:
            continue
        if not (start_d <= d <= end_d):
            continue

        calories += float(m.get("calories", 0))
        macros = m.get("macros", {})
        protein += float(macros.get("protein_g", 0))
        carbs += float(macros.get("carbs_g", 0))
        fat += float(macros.get("fat_g", 0))

    total_macros = protein + carbs + fat
    pct = {
        "protein_pct": (protein / total_macros * 100) if total_macros else 0,
        "carbs_pct": (carbs / total_macros * 100) if total_macros else 0,
        "fat_pct": (fat / total_macros * 100) if total_macros else 0,
    }

    return {
        "range": {"start": start, "end": end},
        "calories": round(calories, 1),
        "protein_g": round(protein, 1),
        "carbs_g": round(carbs, 1),
        "fat_g": round(fat, 1),
        "percentages": {k: round(v, 1) for k, v in pct.items()},
    }
