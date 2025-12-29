from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, date
from typing import Tuple


DATA_FILES = {
    "users": "users.json",
    "workouts": "workouts.json",
    "nutrition": "nutrition.json",
    "metrics": "metrics.json",
}


def _ensure_dirs(base_dir: str, backup_dir: str) -> None:
    os.makedirs(base_dir, exist_ok=True)
    os.makedirs(os.path.join(base_dir, "data"), exist_ok=True)
    os.makedirs(backup_dir, exist_ok=True)


def _json_path(base_dir: str, key: str) -> str:
    return os.path.join(base_dir, "data", DATA_FILES[key])


def _read_json(path: str) -> list:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            return []


def _write_json(path: str, data: list) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def backup_state(base_dir: str, backup_dir: str) -> list[str]:
    _ensure_dirs(base_dir, backup_dir)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    created: list[str] = []
    data_dir = os.path.join(base_dir, "data")

    for fname in DATA_FILES.values():
        src = os.path.join(data_dir, fname)
        if os.path.exists(src):
            dst = os.path.join(backup_dir, f"{fname}.{ts}.bak")
            shutil.copy2(src, dst)
            created.append(dst)

    return created


def restore_latest_backup(base_dir: str, backup_dir: str) -> bool:
    _ensure_dirs(base_dir, backup_dir)
    restored_any = False

    for fname in DATA_FILES.values():
        candidates = [f for f in os.listdir(backup_dir) if f.startswith(fname + ".") and f.endswith(".bak")]
        if not candidates:
            continue
        candidates.sort(reverse=True)
        newest = candidates[0]
        src = os.path.join(backup_dir, newest)
        dst = os.path.join(base_dir, "data", fname)
        shutil.copy2(src, dst)
        restored_any = True

    return restored_any


def load_state(base_dir: str) -> Tuple[list, list, list, list]:
    os.makedirs(os.path.join(base_dir, "data"), exist_ok=True)
    users = _read_json(_json_path(base_dir, "users"))
    workouts = _read_json(_json_path(base_dir, "workouts"))
    meals = _read_json(_json_path(base_dir, "nutrition"))
    metrics = _read_json(_json_path(base_dir, "metrics"))
    return users, workouts, meals, metrics


def save_state(base_dir: str, users: list, workouts: list, meals: list, metrics: list) -> None:
    backup_dir = os.path.join(base_dir, "backups")
    backup_state(base_dir, backup_dir)

    _write_json(_json_path(base_dir, "users"), users)
    _write_json(_json_path(base_dir, "workouts"), workouts)
    _write_json(_json_path(base_dir, "nutrition"), meals)
    _write_json(_json_path(base_dir, "metrics"), metrics)


def parse_date_yyyy_mm_dd(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def parse_datetime_yyyy_mm_dd_hhmm(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d %H:%M")


def validate_workout_entry(entry: dict) -> bool:
    required = ["id", "user_id", "date", "type", "duration_min", "exercises"]
    if any(k not in entry for k in required):
        return False

    try:
        d = parse_date_yyyy_mm_dd(entry["date"])
        if d > date.today() and not entry.get("allow_future", False):
            return False
    except Exception:
        return False

    try:
        if float(entry["duration_min"]) <= 0:
            return False
    except Exception:
        return False

    if entry["type"] not in ("strength", "cardio", "flexibility"):
        return False

    return isinstance(entry.get("exercises", []), list)


def validate_meal_entry(entry: dict) -> bool:
    required = ["id", "user_id", "timestamp", "meal_type", "items", "calories", "macros"]
    if any(k not in entry for k in required):
        return False

    try:
        ts = parse_datetime_yyyy_mm_dd_hhmm(entry["timestamp"])
        if ts.date() > date.today() and not entry.get("allow_future", False):
            return False
    except Exception:
        return False

    try:
        if float(entry["calories"]) < 0:
            return False
    except Exception:
        return False

    macros = entry.get("macros", {})
    for mk in ("protein_g", "carbs_g", "fat_g"):
        if mk not in macros:
            return False
        try:
            if float(macros[mk]) < 0:
                return False
        except Exception:
            return False

    return entry["meal_type"] in ("breakfast", "lunch", "dinner", "snack")


def validate_metric_entry(entry: dict) -> bool:
    required = ["id", "user_id", "date", "type", "value"]
    if any(k not in entry for k in required):
        return False

    try:
        d = parse_date_yyyy_mm_dd(entry["date"])
        if d > date.today() and not entry.get("allow_future", False):
            return False
    except Exception:
        return False

    if entry["type"] not in ("weight_kg", "sleep_hours", "water_l", "mood", "waist_cm", "chest_cm"):
        return False

    try:
        v = float(entry["value"])
        if entry["type"] == "mood":
            return 1 <= v <= 10
        return v > 0
    except Exception:
        return False


def prevent_duplicate(entries: list[dict], keys: list[str], candidate: dict) -> bool:
    for e in entries:
        if all(e.get(k) == candidate.get(k) for k in keys):
            return True
    return False
