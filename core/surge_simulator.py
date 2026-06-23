import json
import random
from pathlib import Path
from core.threshold_adapter import SYSTEMS, get_confidence_decay

BASE_DIR = Path(__file__).parent.parent

SIMULATION_MULTIPLIERS = [10, 50, 100]


def simulate_system_at_volume(system_name: str, volume_multiplier: float) -> dict:
    system = SYSTEMS.get(system_name, {})
    failure_mult = system.get("failure_threshold_multiplier", 8)
    critical_mult = system.get("critical_threshold_multiplier", 6)

    capacity_used_pct = min((volume_multiplier / failure_mult) * 100, 110)
    noise = random.uniform(-3, 3)
    capacity_used_pct = round(capacity_used_pct + noise, 1)

    if volume_multiplier >= failure_mult:
        status = "failure"
        failure_type = _predict_failure_type(system_name, volume_multiplier)
    elif volume_multiplier >= critical_mult:
        status = "critical"
        failure_type = "approaching_limit"
    elif volume_multiplier >= critical_mult * 0.7:
        status = "warning"
        failure_type = None
    else:
        status = "stable"
        failure_type = None

    confidence = get_confidence_decay(volume_multiplier)

    return {
        "system": system_name,
        "display_name": system.get("name", system_name),
        "volume_multiplier": volume_multiplier,
        "capacity_used_pct": min(capacity_used_pct, 100),
        "status": status,
        "failure_type": failure_type,
        "confidence": confidence,
        "time_to_failure_minutes": _estimate_time_to_fail(system, volume_multiplier)
    }


def _predict_failure_type(system_name: str, volume_multiplier: float) -> str:
    failure_types = {
        "order_gateway": "capacity_breach",
        "settlement_engine": "timeout",
        "kafka_consumer": "lag_spike",
        "risk_engine": "queue_overflow",
        "eks_pods": "oomkilled"
    }
    return failure_types.get(system_name, "unknown_failure")


def _estimate_time_to_fail(system: dict, volume_multiplier: float) -> float:
    failure_mult = system.get("failure_threshold_multiplier", 8)
    if volume_multiplier < failure_mult:
        return None
    excess_ratio = volume_multiplier / failure_mult
    base_time = 30 / excess_ratio
    return round(max(2, base_time + random.uniform(-2, 2)), 1)


def run_full_simulation(company: str = "SpaceX") -> dict:
    results = {}
    for multiplier in SIMULATION_MULTIPLIERS:
        scenario = {
            "multiplier": multiplier,
            "label": f"{multiplier}x normal volume",
            "systems": {},
            "overall_status": "stable",
            "failure_count": 0
        }
        failure_count = 0
        statuses = []
        for system_name in SYSTEMS.keys():
            sim = simulate_system_at_volume(system_name, multiplier)
            scenario["systems"][system_name] = sim
            statuses.append(sim["status"])
            if sim["status"] == "failure":
                failure_count += 1

        scenario["failure_count"] = failure_count
        if failure_count >= 3:
            scenario["overall_status"] = "critical"
        elif failure_count >= 1 or "critical" in statuses:
            scenario["overall_status"] = "warning"
        elif "warning" in statuses:
            scenario["overall_status"] = "elevated"
        else:
            scenario["overall_status"] = "stable"

        results[f"{multiplier}x"] = scenario

    return {
        "company": company,
        "scenarios": results,
        "max_safe_multiplier": _calculate_max_safe(results)
    }


def _calculate_max_safe(results: dict) -> float:
    if results.get("10x", {}).get("overall_status") == "stable":
        if results.get("50x", {}).get("overall_status") in ["stable", "elevated"]:
            return 50
        return 10
    return 5


def generate_readiness_score(simulation: dict, similar_events: list) -> dict:
    scores = {}
    max_safe = simulation.get("max_safe_multiplier", 10)

    if max_safe >= 50:
        scores["simulation"] = 80
    elif max_safe >= 10:
        scores["simulation"] = 55
    else:
        scores["simulation"] = 30

    historical_scores = [e.get("readiness_score", 70) for e in similar_events]
    scores["historical"] = sum(historical_scores) / len(historical_scores) if historical_scores else 65

    total_failures = sum(
        s.get("failure_count", 0)
        for s in simulation.get("scenarios", {}).values()
    )
    scores["failure_risk"] = max(0, 100 - (total_failures * 12))

    final_score = round(
        scores["simulation"] * 0.5 +
        scores["historical"] * 0.3 +
        scores["failure_risk"] * 0.2
    )

    if final_score >= 80:
        risk_level = "Low"
        risk_color = "success"
    elif final_score >= 60:
        risk_level = "Medium"
        risk_color = "warning"
    elif final_score >= 40:
        risk_level = "High"
        risk_color = "danger"
    else:
        risk_level = "Critical"
        risk_color = "danger"

    return {
        "score": final_score,
        "risk_level": risk_level,
        "risk_color": risk_color,
        "component_scores": scores
    }
