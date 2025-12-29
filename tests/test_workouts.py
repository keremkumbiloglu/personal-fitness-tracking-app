from workouts import log_workout, detect_and_flag_prs, personal_records


def test_personal_record_strength():
    workouts = []
    user_id = "u1"

    w1 = log_workout(workouts, {
        "user_id": user_id,
        "date": "2025-01-01",
        "type": "strength",
        "duration_min": 45,
        "exercises": [{"name": "Bench Press", "sets": 3, "reps": 5, "weight_kg": 60}],
    })
    detect_and_flag_prs(workouts, user_id, w1)
    assert any("Heaviest" in x for x in w1.get("pr_flags", []))

    w2 = log_workout(workouts, {
        "user_id": user_id,
        "date": "2025-01-08",
        "type": "strength",
        "duration_min": 45,
        "exercises": [{"name": "Bench Press", "sets": 3, "reps": 5, "weight_kg": 55}],
    })
    detect_and_flag_prs(workouts, user_id, w2)
    assert len(w2.get("pr_flags", [])) == 0

    prs = personal_records(workouts, user_id)
    assert prs["max_lift_kg"] == 60.0
    assert prs["max_lift_exercise"] == "Bench Press"
