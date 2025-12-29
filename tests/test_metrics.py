from metrics import log_metric, goal_progress


def test_goal_progress_weight_loss():
    users = [{
        "id": "u1",
        "goal": {"type": "weight_loss", "target_weight_kg": 70, "daily_calorie_goal": None, "start_date": "2025-01-01", "end_date": None}
    }]
    metrics = []
    log_metric(metrics, {"user_id": "u1", "date": "2025-01-01", "type": "weight_kg", "value": 80})
    log_metric(metrics, {"user_id": "u1", "date": "2025-01-15", "type": "weight_kg", "value": 78})

    gp = goal_progress(users, metrics, "u1")
    assert gp["progress_pct"] is not None
    assert gp["start_weight_kg"] == 80.0
    assert gp["current_weight_kg"] == 78.0
    assert gp["target_weight_kg"] == 70.0
