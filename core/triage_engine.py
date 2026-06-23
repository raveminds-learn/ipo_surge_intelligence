from core.threshold_adapter import evaluate_system_health, get_adaptive_thresholds

RESOLUTION_PLAYBOOK = {
    "kafka_consumer": {
        "lag_spike": {
            "action": "Restart Kafka consumer group B immediately",
            "estimated_fix_minutes": 3,
            "escalate": False
        }
    },
    "order_gateway": {
        "capacity_breach": {
            "action": "Scale order gateway pods — add 4 pods minimum",
            "estimated_fix_minutes": 5,
            "escalate": True
        }
    },
    "settlement_engine": {
        "timeout": {
            "action": "Increase settlement timeout to 60s + enable async mode",
            "estimated_fix_minutes": 10,
            "escalate": True
        }
    },
    "risk_engine": {
        "queue_overflow": {
            "action": "Enable async risk scoring for retail orders",
            "estimated_fix_minutes": 8,
            "escalate": False
        }
    },
    "eks_pods": {
        "oomkilled": {
            "action": "Increase pod memory limits + restart affected pods",
            "estimated_fix_minutes": 4,
            "escalate": False
        }
    }
}

PRIORITY_WEIGHTS = {
    "kafka_consumer": 10,
    "order_gateway": 9,
    "settlement_engine": 8,
    "eks_pods": 7,
    "risk_engine": 6
}

STATUS_WEIGHTS = {
    "critical": 100,
    "warning": 50,
    "healthy": 0,
    "unknown": 20
}


def triage_systems(system_metrics: dict, volume_multiplier: float) -> list:
    thresholds = get_adaptive_thresholds(volume_multiplier)
    triage_items = []

    for system_name, metrics in system_metrics.items():
        for metric_name, metric_value in metrics.items():
            health = evaluate_system_health(
                system_name, metric_value, metric_name, volume_multiplier
            )
            if health["status"] in ["critical", "warning"]:
                priority_score = (
                    STATUS_WEIGHTS.get(health["status"], 0) +
                    PRIORITY_WEIGHTS.get(system_name, 5)
                )
                playbook = _get_playbook(system_name, health["status"])
                triage_items.append({
                    "system": system_name,
                    "display_name": _display_name(system_name),
                    "metric": metric_name,
                    "status": health["status"],
                    "current_value": metric_value,
                    "threshold": health.get("threshold"),
                    "priority_score": priority_score,
                    "action": playbook.get("action", "Investigate immediately"),
                    "estimated_fix_minutes": playbook.get("estimated_fix_minutes", 10),
                    "escalate": playbook.get("escalate", False),
                    "volume_band": thresholds["volume_band"],
                    "threshold_adapted": True
                })

    triage_items.sort(key=lambda x: x["priority_score"], reverse=True)
    for i, item in enumerate(triage_items):
        item["priority_rank"] = i + 1

    return triage_items


def _get_playbook(system_name: str, status: str) -> dict:
    system_plays = RESOLUTION_PLAYBOOK.get(system_name, {})
    if status == "critical":
        return next(iter(system_plays.values()), {})
    return {}


def _display_name(system_name: str) -> str:
    names = {
        "order_gateway": "Order Gateway",
        "settlement_engine": "Settlement Engine",
        "kafka_consumer": "Kafka Consumer",
        "risk_engine": "Risk Engine",
        "eks_pods": "EKS Pods"
    }
    return names.get(system_name, system_name)


def distinguish_surge_vs_failure(system_name: str, metric_value: float,
                                  metric: str, volume_multiplier: float) -> dict:
    health = evaluate_system_health(system_name, metric_value, metric, volume_multiplier)
    band = health.get("volume_band", "normal")

    if health["status"] == "healthy":
        classification = "expected_surge_behaviour"
        explanation = f"Within adaptive threshold for {band} volume ({volume_multiplier:.0f}x). No action needed."
    elif health["status"] == "warning" and band in ["surge", "critical"]:
        classification = "expected_surge_behaviour"
        explanation = f"Elevated but within expected range for {volume_multiplier:.0f}x surge. Monitor closely."
    elif health["status"] == "critical":
        classification = "genuine_failure"
        explanation = f"Exceeds adapted threshold for {band} volume. Immediate action required."
    else:
        classification = "investigate"
        explanation = "Borderline — review manually."

    return {
        "system": system_name,
        "classification": classification,
        "explanation": explanation,
        "status": health["status"],
        "volume_band": band
    }
