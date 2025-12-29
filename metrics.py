from __future__ import annotations

import uuid
from datetime import datetime, timedelta


def log_metric(metrics: list, metric_data: dict) -> dict:
    entry = dict(metric_data)
    entry["id"] = entry.get("id") or str(uuid.uuid4())
    entry.setdefault("allow_future", False)
    metrics.append(entry)
    return entry


def metrics_summary(metrics: list, user_id: str, metric_type: str, period: tuple[str, str]) -> dict:
    start, end = period
    start_d = datetime.strptime(start, "%Y-%m-%d").date()
    end_d = datetime.strptime(end, "%Y-%m-%d").date()

    values = []
    for e in metrics:
        if e.get("user_id") != user_id or e.get("type") != metric_type:
            continue
        try:
            d = datetime.strptime(e.get("date", ""), "%Y-%m-%d").date()
        except Exception:
            continue
        if start_d <= d <= end_d:
            values.append((d, float(e.get("value"))))

    values.sort(key=lambda x: x[0])

    if not values:
        return {"type": metric_type, "period": {"start": start, "end": end}, "count": 0, "min": None, "max": None, "avg": None, "values": []}

    only = [v for _, v in values]
    return {
        "type": metric_type,
        "period": {"start": start, "end": end},
        "count": len(only),
        "min": round(min(only), 2),
        "max": round(max(only), 2),
        "avg": round(sum(only) / len(only), 2),
        "values": [{"date": d.strftime("%Y-%m-%d"), "value": v} for d, v in values],
    }


def goal_progress(users: list, metrics: list, user_id: str) -> dict:
    user = next((u for u in users if u.get("id") == user_id), None)
    if not user:
        raise ValueError("User not found.")

    goal = user.get("goal", {})
    gtype = goal.get("type", "maintenance")
    target = goal.get("target_weight_kg")

    weights = []
    for e in metrics:
        if e.get("user_id") == user_id and e.get("type") == "weight_kg":
            try:
                d = datetime.strptime(e.get("date", ""), "%Y-%m-%d").date()
                weights.append((d, float(e.get("value"))))
            except Exception:
                pass
    weights.sort(key=lambda x: x[0])

    if not weights:
        return {"goal_type": gtype, "message": "No weight data yet.", "progress_pct": None, "projected_end_date": None}

    start_weight = weights[0][1]
    current_weight = weights[-1][1]
    current_date = weights[-1][0]

    if gtype in ("weight_loss", "muscle_gain") and target:
        target = float(target)
        total_needed = abs(target - start_weight)
        done = abs(current_weight - start_weight)
        progress = (done / total_needed * 100) if total_needed else 100.0
        progress = max(0.0, min(100.0, progress))

        last_n = [x for x in weights if x[0] >= (current_date - timedelta(days=14))]
        if len(last_n) >= 2:
            days = (last_n[-1][0] - last_n[0][0]).days or 1
            delta = last_n[-1][1] - last_n[0][1]
            daily = delta / days
        else:
            daily = 0.0

        projected = None
        if daily != 0:
            remaining = target - current_weight
            if (remaining < 0 and daily < 0) or (remaining > 0 and daily > 0):
                days_needed = int(abs(remaining / daily))
                projected = (current_date + timedelta(days=days_needed)).strftime("%Y-%m-%d")

        return {
            "goal_type": gtype,
            "start_weight_kg": round(start_weight, 2),
            "current_weight_kg": round(current_weight, 2),
            "target_weight_kg": round(target, 2),
            "progress_pct": round(progress, 1),
            "projected_end_date": projected,
        }

    return {"goal_type": gtype, "message": "Goal type is not weight-based or target not set.", "progress_pct": None, "projected_end_date": None}


def moving_average(values: list[float], window: int = 7) -> list[float]:
    if window <= 1:
        return values[:]
    out = []
    for i in range(len(values)):
        start = max(0, i - window + 1)
        chunk = values[start : i + 1]
        out.append(sum(chunk) / len(chunk))
    return out


def generate_ascii_chart(values: list[float]) -> str:
    if not values:
        return "(no data)"
    blocks = "▁▂▃▄▅▆▇█"
    mn = min(values)
    mx = max(values)
    if mx == mn:
        return blocks[0] * len(values)
    chars = []
    for v in values:
        idx = int((v - mn) / (mx - mn) * (len(blocks) - 1))
        chars.append(blocks[idx])
    return "".join(chars)
