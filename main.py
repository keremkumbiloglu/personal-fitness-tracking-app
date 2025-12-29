from __future__ import annotations

import os
from datetime import date, datetime

from storage import (
    load_state,
    save_state,
    restore_latest_backup,
    validate_workout_entry,
    validate_meal_entry,
    validate_metric_entry,
    prevent_duplicate,
)
from profiles import register_user, authenticate_user, update_goal
from workouts import (
    log_workout,
    update_workout,
    delete_workout,
    weekly_workout_summary,
    personal_records,
    detect_and_flag_prs,
)
from nutrition import log_meal, update_meal, delete_meal, daily_calorie_summary, macro_breakdown
from metrics import log_metric, metrics_summary, goal_progress, moving_average, generate_ascii_chart


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def prompt(msg: str) -> str:
    return input(msg).strip()


def prompt_float(msg: str, min_val: float | None = None, max_val: float | None = None) -> float:
    while True:
        s = prompt(msg)
        try:
            v = float(s)
            if min_val is not None and v < min_val:
                print(f"Value must be >= {min_val}.")
                continue
            if max_val is not None and v > max_val:
                print(f"Value must be <= {max_val}.")
                continue
            return v
        except ValueError:
            print("Please enter a valid number.")


def prompt_int(msg: str, min_val: int | None = None, max_val: int | None = None) -> int:
    while True:
        s = prompt(msg)
        try:
            v = int(s)
            if min_val is not None and v < min_val:
                print(f"Value must be >= {min_val}.")
                continue
            if max_val is not None and v > max_val:
                print(f"Value must be <= {max_val}.")
                continue
            return v
        except ValueError:
            print("Please enter a valid integer.")


def prompt_date(msg: str) -> str:
    while True:
        s = prompt(msg + " (YYYY-MM-DD): ")
        try:
            datetime.strptime(s, "%Y-%m-%d")
            return s
        except ValueError:
            print("Invalid date format. Use YYYY-MM-DD.")


def prompt_timestamp(msg: str) -> str:
    while True:
        s = prompt(msg + " (YYYY-MM-DD HH:MM): ")
        try:
            datetime.strptime(s, "%Y-%m-%d %H:%M")
            return s
        except ValueError:
            print("Invalid timestamp format. Use YYYY-MM-DD HH:MM.")


def divider() -> None:
    print("-" * 60)


def dashboard(user: dict, users: list, workouts: list, meals: list, metrics: list) -> None:
    divider()
    today = date.today().strftime("%Y-%m-%d")
    print(f"Dashboard — {user['name']} ({today})")
    divider()

    todays_ws = [w for w in workouts if w.get("user_id") == user["id"] and w.get("date") == today]
    print(f"Workouts today: {len(todays_ws)}")
    if todays_ws:
        for w in todays_ws:
            print(f" - {w.get('type')} {w.get('duration_min')} min | PRs: {len(w.get('pr_flags', []))}")
    else:
        recent = []
        for w in workouts:
            if w.get("user_id") != user["id"]:
                continue
            try:
                d = datetime.strptime(w.get("date", ""), "%Y-%m-%d").date()
                recent.append(d)
            except Exception:
                pass
        if recent:
            last = max(recent)
            if (date.today() - last).days >= 3:
                print("Reminder: No workout recorded for 3+ days.")
        else:
            print("Reminder: No workouts logged yet.")

    cal = daily_calorie_summary(meals, user["id"], today)
    print(f"Calories today: {cal['total_calories']}")

    goal_cals = user.get("goal", {}).get("daily_calorie_goal")
    if goal_cals:
        diff = cal["total_calories"] - float(goal_cals)
        status = "surplus" if diff > 0 else "deficit"
        print(f"Calorie goal: {goal_cals} → {abs(diff):.1f} {status}")

    try:
        gp = goal_progress(users, metrics, user["id"])
        if gp.get("progress_pct") is not None:
            print(f"Goal progress: {gp['progress_pct']}% (target {gp.get('target_weight_kg')} kg)")
            if gp.get("projected_end_date"):
                print(f"Projected completion: {gp['projected_end_date']}")
        else:
            print(f"Goal progress: {gp.get('message', 'N/A')}")
    except Exception:
        print("Goal progress: N/A")

    divider()


def register_flow(users: list) -> dict | None:
    divider()
    print("Register New User")
    divider()
    profile = {
        "name": prompt("Name: "),
        "email": prompt("Email: "),
        "pin": prompt("PIN (4-6 digits): "),
        "age": prompt_int("Age: ", 1, 120),
        "height_cm": prompt_float("Height (cm): ", 50, 250),
        "weight_kg": prompt_float("Weight (kg): ", 20, 400),
        "activity_level": (prompt("Activity level (low/moderate/high): ").lower() or "moderate"),
    }
    try:
        user = register_user(users, profile)
        print("✅ Registered successfully.")
        return user
    except Exception as e:
        print(f"❌ Registration failed: {e}")
        return None


def login_flow(users: list) -> dict | None:
    divider()
    print("Login")
    divider()
    email = prompt("Email: ")
    pin = prompt("PIN: ")
    user = authenticate_user(users, email, pin)
    if user:
        print("✅ Logged in.")
        return user
    print("❌ Invalid credentials.")
    return None


def goal_menu(users: list, user: dict) -> None:
    divider()
    print("Update Goal")
    divider()
    print("Goal types: weight_loss, muscle_gain, endurance, maintenance")
    gtype = (prompt("Goal type: ").lower() or user["goal"].get("type", "maintenance"))

    target = None
    if gtype in ("weight_loss", "muscle_gain"):
        target = prompt_float("Target weight (kg): ", 20, 400)

    cals = prompt("Daily calorie goal (optional, press enter to skip): ")
    calorie_goal = float(cals) if cals.strip() else None

    start = prompt_date("Start date")
    end = prompt("End date (optional YYYY-MM-DD, press enter to skip): ").strip() or None

    update_goal(users, user["id"], {
        "type": gtype,
        "target_weight_kg": target,
        "daily_calorie_goal": calorie_goal,
        "start_date": start,
        "end_date": end,
    })
    print("✅ Goal updated.")


def workout_menu(workouts: list, user: dict) -> None:
    while True:
        divider()
        print("Workout Menu")
        print("1) Log workout")
        print("2) Update workout")
        print("3) Delete workout")
        print("4) Weekly summary")
        print("5) Personal records")
        print("0) Back")
        choice = prompt("> ")

        if choice == "1":
            wdate = prompt_date("Workout date")
            wtype = prompt("Type (strength/cardio/flexibility): ").lower()
            duration = prompt_float("Duration (minutes): ", 1, 1000)
            notes = prompt("Notes (optional): ")

            exercises = []
            print("Add exercises (press enter on name to stop).")
            while True:
                name = prompt("Exercise name: ")
                if not name:
                    break
                ex = {"name": name}
                if wtype == "strength":
                    ex["sets"] = prompt_int("Sets: ", 1, 100)
                    ex["reps"] = prompt_int("Reps: ", 1, 500)
                    ex["weight_kg"] = prompt_float("Weight (kg): ", 0, 500)
                elif wtype == "cardio":
                    ex["distance_km"] = prompt_float("Distance (km): ", 0, 200)
                    ex["time_min"] = prompt_float("Time (min): ", 0.1, 2000)
                else:
                    ex["minutes"] = prompt_float("Minutes: ", 0.1, 1000)
                exercises.append(ex)

            workout_data = {
                "user_id": user["id"],
                "date": wdate,
                "type": wtype,
                "duration_min": duration,
                "exercises": exercises,
                "notes": notes,
                "allow_future": False,
            }

            if not validate_workout_entry({"id": "tmp", **workout_data}):
                print("❌ Invalid workout entry.")
                continue
            if prevent_duplicate(workouts, ["user_id", "date", "type"], workout_data):
                print("❌ Duplicate workout (same date & type).")
                continue

            w = log_workout(workouts, workout_data)
            detect_and_flag_prs(workouts, user["id"], w)
            print("✅ Workout logged.")
            if w.get("pr_flags"):
                print("🎉 PRs detected:")
                for f in w["pr_flags"]:
                    print(" -", f)

        elif choice == "2":
            wid = prompt("Workout ID: ")
            field = prompt("Field to update (date/type/duration_min/notes): ")
            value = prompt("New value: ")
            try:
                update_workout(workouts, wid, {field: value})
                print("✅ Updated.")
            except Exception as e:
                print("❌", e)

        elif choice == "3":
            wid = prompt("Workout ID to delete: ")
            if prompt("Type DELETE to confirm: ") != "DELETE":
                print("Cancelled.")
                continue
            ok = delete_workout(workouts, wid)
            print("✅ Deleted." if ok else "❌ Not found.")

        elif choice == "4":
            ws = prompt_date("Week start (recommend Monday)")
            print(weekly_workout_summary(workouts, user["id"], ws))

        elif choice == "5":
            print(personal_records(workouts, user["id"]))

        elif choice == "0":
            return
        else:
            print("Invalid choice.")


def nutrition_menu(meals: list, user: dict) -> None:
    while True:
        divider()
        print("Nutrition Menu")
        print("1) Log meal")
        print("2) Update meal")
        print("3) Delete meal")
        print("4) Daily calorie summary")
        print("5) Macro breakdown (date range)")
        print("0) Back")
        choice = prompt("> ")

        if choice == "1":
            ts = prompt_timestamp("Meal timestamp")
            meal_type = prompt("Meal type (breakfast/lunch/dinner/snack): ").lower()

            items = []
            print("Add food items (press enter on item name to stop).")
            while True:
                name = prompt("Item name: ")
                if not name:
                    break
                grams = prompt_float("Grams (approx): ", 0, 5000)
                items.append({"name": name, "grams": grams})

            calories = prompt_float("Total calories: ", 0, 20000)
            protein = prompt_float("Protein (g): ", 0, 500)
            carbs = prompt_float("Carbs (g): ", 0, 1000)
            fat = prompt_float("Fat (g): ", 0, 500)

            meal_data = {
                "user_id": user["id"],
                "timestamp": ts,
                "meal_type": meal_type,
                "items": items,
                "calories": calories,
                "macros": {"protein_g": protein, "carbs_g": carbs, "fat_g": fat},
                "allow_future": False,
            }

            if not validate_meal_entry({"id": "tmp", **meal_data}):
                print("❌ Invalid meal entry.")
                continue
            if prevent_duplicate(meals, ["user_id", "timestamp", "meal_type"], meal_data):
                print("❌ Duplicate meal (same timestamp & type).")
                continue

            log_meal(meals, meal_data)
            print("✅ Meal logged.")

        elif choice == "2":
            mid = prompt("Meal ID: ")
            field = prompt("Field to update (timestamp/meal_type/calories): ")
            value = prompt("New value: ")
            try:
                update_meal(meals, mid, {field: value})
                print("✅ Updated.")
            except Exception as e:
                print("❌", e)

        elif choice == "3":
            mid = prompt("Meal ID to delete: ")
            if prompt("Type DELETE to confirm: ") != "DELETE":
                print("Cancelled.")
                continue
            ok = delete_meal(meals, mid)
            print("✅ Deleted." if ok else "❌ Not found.")

        elif choice == "4":
            d = prompt_date("Date")
            print(daily_calorie_summary(meals, user["id"], d))

        elif choice == "5":
            start = prompt_date("Start date")
            end = prompt_date("End date")
            print(macro_breakdown(meals, user["id"], (start, end)))

        elif choice == "0":
            return
        else:
            print("Invalid choice.")


def metrics_menu(metrics: list, users: list, user: dict) -> None:
    while True:
        divider()
        print("Metrics Menu")
        print("1) Log metric")
        print("2) Metrics summary")
        print("3) Weight trend (7-day MA + ASCII chart)")
        print("4) Goal progress")
        print("0) Back")
        choice = prompt("> ")

        if choice == "1":
            d = prompt_date("Metric date")
            mtype = prompt("Type (weight_kg/sleep_hours/water_l/mood/waist_cm/chest_cm): ").lower()
            val = prompt_float("Value: ", 0, 1000)
            if mtype == "mood":
                val = max(1, min(10, val))

            entry = {"user_id": user["id"], "date": d, "type": mtype, "value": val, "allow_future": False}

            if not validate_metric_entry({"id": "tmp", **entry}):
                print("❌ Invalid metric entry.")
                continue
            if prevent_duplicate(metrics, ["user_id", "date", "type"], entry):
                print("❌ Duplicate metric (same date & type).")
                continue

            log_metric(metrics, entry)
            print("✅ Metric logged.")

        elif choice == "2":
            mtype = prompt("Metric type: ").lower()
            start = prompt_date("Start date")
            end = prompt_date("End date")
            print(metrics_summary(metrics, user["id"], mtype, (start, end)))

        elif choice == "3":
            weights = []
            for e in metrics:
                if e.get("user_id") == user["id"] and e.get("type") == "weight_kg":
                    try:
                        dt = datetime.strptime(e.get("date", ""), "%Y-%m-%d").date()
                        weights.append((dt, float(e.get("value"))))
                    except Exception:
                        pass
            weights.sort(key=lambda x: x[0])
            if not weights:
                print("No weight data.")
                continue

            vals = [v for _, v in weights][-21:]
            ma = moving_average(vals, 7)
            print("Weight values:", [round(x, 2) for x in vals])
            print("7-day MA:", [round(x, 2) for x in ma])
            print("Chart:", generate_ascii_chart(ma))

        elif choice == "4":
            try:
                print(goal_progress(users, metrics, user["id"]))
            except Exception as e:
                print("❌", e)

        elif choice == "0":
            return
        else:
            print("Invalid choice.")


def list_user_entries(workouts: list, meals: list, metrics: list, user_id: str) -> None:
    divider()
    print("Your Entry IDs (use these for update/delete)")
    divider()
    print("Workouts:")
    for w in workouts:
        if w.get("user_id") == user_id:
            print(f" - {w['id']} | {w.get('date')} | {w.get('type')} | {w.get('duration_min')} min")
    print("Meals:")
    for m in meals:
        if m.get("user_id") == user_id:
            print(f" - {m['id']} | {m.get('timestamp')} | {m.get('meal_type')} | {m.get('calories')} cal")
    print("Metrics:")
    for e in metrics:
        if e.get("user_id") == user_id:
            print(f" - {e['id']} | {e.get('date')} | {e.get('type')} = {e.get('value')}")
    divider()


def main() -> None:
    users, workouts, meals, metrics = load_state(BASE_DIR)
    current_user = None
    unsaved = False

    while True:
        divider()
        print("Personal Fitness Tracking App")
        print("1) Register")
        print("2) Login")
        print("3) Restore latest backup")
        print("0) Exit")
        choice = prompt("> ")

        if choice == "1":
            u = register_flow(users)
            if u:
                current_user = u
                unsaved = True
        elif choice == "2":
            u = login_flow(users)
            if u:
                current_user = u
        elif choice == "3":
            ok = restore_latest_backup(BASE_DIR, os.path.join(BASE_DIR, "backups"))
            print("✅ Restored." if ok else "No backups found.")
            users, workouts, meals, metrics = load_state(BASE_DIR)
            unsaved = False
        elif choice == "0":
            if unsaved and prompt("Unsaved changes. Save before exit? (y/n): ").lower() == "y":
                save_state(BASE_DIR, users, workouts, meals, metrics)
                print("✅ Saved.")
            print("Bye.")
            return
        else:
            print("Invalid choice.")
            continue

        while current_user:
            dashboard(current_user, users, workouts, meals, metrics)
            print("User Menu")
            print("1) Workouts")
            print("2) Nutrition")
            print("3) Metrics")
            print("4) Goals")
            print("5) List my entry IDs")
            print("6) Save now")
            print("7) Switch user (logout)")
            print("0) Exit app")
            c = prompt("> ")

            if c == "1":
                workout_menu(workouts, current_user); unsaved = True
            elif c == "2":
                nutrition_menu(meals, current_user); unsaved = True
            elif c == "3":
                metrics_menu(metrics, users, current_user); unsaved = True
            elif c == "4":
                goal_menu(users, current_user); unsaved = True
            elif c == "5":
                list_user_entries(workouts, meals, metrics, current_user["id"])
            elif c == "6":
                save_state(BASE_DIR, users, workouts, meals, metrics)
                unsaved = False
                print("✅ Saved.")
            elif c == "7":
                if unsaved and prompt("Unsaved changes. Save before logout? (y/n): ").lower() == "y":
                    save_state(BASE_DIR, users, workouts, meals, metrics)
                    unsaved = False
                    print("✅ Saved.")
                current_user = None
            elif c == "0":
                if unsaved and prompt("Unsaved changes. Save before exit? (y/n): ").lower() == "y":
                    save_state(BASE_DIR, users, workouts, meals, metrics)
                    print("✅ Saved.")
                return
            else:
                print("Invalid choice.")


if __name__ == "__main__":
    main()
