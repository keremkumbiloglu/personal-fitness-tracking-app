from __future__ import annotations

import uuid
from datetime import datetime, timedelta


def log_workout(workouts: list, workout_data: dict) -> dict:
    workout = dict(workout_data)
    workout["id"] = workout.get("id") or str(uuid.uuid4())
    workout.setdefault("notes", "")
    workout.setdefault("allow_future", False)
    workout.setdefault("pr_flags", [])
    workouts.append(workout)
    return workout


def update_workout(workouts: list, workout_id: str, updates: dict) -> dict:
    w = next((x for x in workouts if x.get("id") == workout_id), None)
    if not w:
        raise ValueError("Workout not found.")
    w.update(updates)
    return w


def delete_workout(workouts: list, workout_id: str) -> bool:
    idx = next((i for i, x in enumerate(workouts) if x.get("id") == workout_id), None)
    if idx is None:
        return False
    workouts.pop(idx)
    return True


def _parse_date(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d")


def weekly_workout_summary(workouts: list, user_id: str, week_start: str) -> dict:
    start = _parse_date(week_start)
    end = start + timedelta(days=7)

    user_ws = [w for w in workouts if w.get("user_id") == user_id]
    in_week = []
    for w in user_ws:
        try:
            d = _parse_date(w.get("date", ""))
            if start <= d < end:
                in_week.append(w)
        except Exception:
            continue

    total_workouts = len(in_week)
    total_minutes = sum(float(w.get("duration_min", 0)) for w in in_week)

    weights = {"strength": 2.0, "cardio": 1.5, "flexibility": 1.0}
    intensity_score = sum(weights.get(w.get("type"), 1.0) * float(w.get("duration_min", 0)) for w in in_week)

    by_type = {"strength": 0, "cardio": 0, "flexibility": 0}
    for w in in_week:
        t = w.get("type")
        if t in by_type:
            by_type[t] += 1

    return {
        "week_start": week_start,
        "week_end": (end - timedelta(days=1)).strftime("%Y-%m-%d"),
        "total_workouts": total_workouts,
        "total_minutes": round(total_minutes, 1),
        "intensity_score": round(intensity_score, 1),
        "by_type": by_type,
    }


def personal_records(workouts: list, user_id: str) -> dict:
    user_ws = [w for w in workouts if w.get("user_id") == user_id]
    max_lift = 0.0
    max_lift_ex = None
    best_pace = None
    best_cardio = None

    for w in user_ws:
        if w.get("type") == "strength":
            for ex in w.get("exercises", []):
                try:
                    weight = float(ex.get("weight_kg", 0))
                    if weight > max_lift:
                        max_lift = weight
                        max_lift_ex = ex.get("name")
                except Exception:
                    pass

        if w.get("type") == "cardio":
            for ex in w.get("exercises", []):
                try:
                    dist = float(ex.get("distance_km", 0))
                    tmin = float(ex.get("time_min", 0))
                    if dist > 0 and tmin > 0:
                        pace = tmin / dist
                        if best_pace is None or pace < best_pace:
                            best_pace = pace
                            best_cardio = {
                                "name": ex.get("name"),
                                "distance_km": dist,
                                "time_min": tmin,
                                "pace_min_per_km": pace,
                            }
                except Exception:
                    pass

    return {
        "max_lift_kg": round(max_lift, 1) if max_lift_ex else None,
        "max_lift_exercise": max_lift_ex,
        "best_cardio": (
            None
            if best_cardio is None
            else {
                "name": best_cardio["name"],
                "distance_km": round(best_cardio["distance_km"], 2),
                "time_min": round(best_cardio["time_min"], 1),
                "pace_min_per_km": round(best_cardio["pace_min_per_km"], 2),
            }
        ),
    }


def detect_and_flag_prs(workouts: list, user_id: str, new_workout: dict) -> dict:
    flags = []

    if new_workout.get("type") == "strength":
        prev_max = 0.0
        for w in workouts:
            if w.get("user_id") != user_id or w.get("id") == new_workout.get("id"):
                continue
            if w.get("type") != "strength":
                continue
            for ex in w.get("exercises", []):
                try:
                    prev_max = max(prev_max, float(ex.get("weight_kg", 0)))
                except Exception:
                    pass

        new_max = 0.0
        new_max_name = None
        for ex in new_workout.get("exercises", []):
            try:
                wkg = float(ex.get("weight_kg", 0))
                if wkg > new_max:
                    new_max = wkg
                    new_max_name = ex.get("name")
            except Exception:
                pass

        if new_max_name and new_max > prev_max:
            flags.append(f"PR: Heaviest lift {new_max} kg ({new_max_name})")

    if new_workout.get("type") == "cardio":
        prev_best_pace = None
        for w in workouts:
            if w.get("user_id") != user_id or w.get("id") == new_workout.get("id"):
                continue
            if w.get("type") != "cardio":
                continue
            for ex in w.get("exercises", []):
                try:
                    dist = float(ex.get("distance_km", 0))
                    tmin = float(ex.get("time_min", 0))
                    if dist > 0 and tmin > 0:
                        pace = tmin / dist
                        if prev_best_pace is None or pace < prev_best_pace:
                            prev_best_pace = pace
                except Exception:
                    pass

        new_best_pace = None
        new_best_desc = None
        for ex in new_workout.get("exercises", []):
            try:
                dist = float(ex.get("distance_km", 0))
                tmin = float(ex.get("time_min", 0))
                if dist > 0 and tmin > 0:
                    pace = tmin / dist
                    if new_best_pace is None or pace < new_best_pace:
                        new_best_pace = pace
                        new_best_desc = f"{ex.get('name')} {dist}km in {tmin}min (pace {pace:.2f} min/km)"
            except Exception:
                pass

        if new_best_pace is not None and (prev_best_pace is None or new_best_pace < prev_best_pace):
            flags.append(f"PR: Fastest pace — {new_best_desc}")

    new_workout["pr_flags"] = flags
    return new_workout
