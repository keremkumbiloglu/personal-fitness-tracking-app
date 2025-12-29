from __future__ import annotations

import uuid
from datetime import date, datetime


def load_users(path: str) -> list:
    import json, os
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_users(path: str, users: list) -> None:
    import json, os
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)


def register_user(users: list, profile: dict) -> dict:
    email = profile.get("email", "").strip().lower()
    if not email or "@" not in email:
        raise ValueError("Invalid email.")
    if any(u.get("email") == email for u in users):
        raise ValueError("Email already registered.")

    pin = str(profile.get("pin", "")).strip()
    if not (pin.isdigit() and 4 <= len(pin) <= 6):
        raise ValueError("PIN must be 4-6 digits.")

    try:
        age = int(profile.get("age"))
        height = float(profile.get("height_cm"))
        weight = float(profile.get("weight_kg"))
    except Exception as exc:
        raise ValueError("Age/height/weight must be numeric.") from exc
    if age <= 0 or height <= 0 or weight <= 0:
        raise ValueError("Age/height/weight must be > 0.")

    activity = (profile.get("activity_level") or "moderate").lower()
    if activity not in ("low", "moderate", "high"):
        raise ValueError("Activity level must be: low/moderate/high.")

    user = {
        "id": str(uuid.uuid4()),
        "name": (str(profile.get("name", "")).strip().title() or "User"),
        "email": email,
        "pin": pin,
        "age": age,
        "height_cm": height,
        "weight_kg": weight,
        "activity_level": activity,
        "goal": {
            "type": "maintenance",
            "target_weight_kg": None,
            "daily_calorie_goal": None,
            "start_date": date.today().strftime("%Y-%m-%d"),
            "end_date": None,
        },
    }
    users.append(user)
    return user


def authenticate_user(users: list, email: str, pin: str) -> dict | None:
    email = (email or "").strip().lower()
    pin = str(pin or "").strip()
    for u in users:
        if u.get("email") == email and u.get("pin") == pin:
            return u
    return None


def update_goal(users: list, user_id: str, goal_data: dict) -> dict:
    user = next((u for u in users if u.get("id") == user_id), None)
    if not user:
        raise ValueError("User not found.")

    gtype = goal_data.get("type", user["goal"].get("type", "maintenance"))
    if gtype not in ("weight_loss", "muscle_gain", "endurance", "maintenance"):
        raise ValueError("Invalid goal type.")

    start_date_s = goal_data.get("start_date", user["goal"].get("start_date"))
    end_date_s = goal_data.get("end_date", user["goal"].get("end_date"))

    try:
        datetime.strptime(start_date_s, "%Y-%m-%d")
        if end_date_s:
            datetime.strptime(end_date_s, "%Y-%m-%d")
    except Exception as exc:
        raise ValueError("Dates must be YYYY-MM-DD.") from exc

    target_weight = goal_data.get("target_weight_kg", user["goal"].get("target_weight_kg"))
    if target_weight is not None:
        target_weight = float(target_weight)
        if target_weight <= 0:
            raise ValueError("Target weight must be > 0.")

    calorie_goal = goal_data.get("daily_calorie_goal", user["goal"].get("daily_calorie_goal"))
    if calorie_goal is not None:
        calorie_goal = float(calorie_goal)
        if calorie_goal <= 0:
            raise ValueError("Daily calorie goal must be > 0.")

    user["goal"] = {
        "type": gtype,
        "target_weight_kg": target_weight,
        "daily_calorie_goal": calorie_goal,
        "start_date": start_date_s,
        "end_date": end_date_s,
    }
    return user
