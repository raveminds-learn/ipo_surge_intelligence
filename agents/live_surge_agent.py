import random
import time
import uuid
from core.database import log_surge_metric, get_duckdb
from core.threshold_adapter import get_adaptive_thresholds, get_confidence_decay
from core.triage_engine import triage_systems, distinguish_surge_vs_failure
from core.llm_client import query_mistral_json, SYSTEM_LIVE_SURGE


def generate_live_metrics(volume_multiplier: float) -> dict:
    base = {
        "kafka_consumer": {
            "kafka_lag": _simulate_kafka_lag(volume_multiplier),
        },
        "order_gateway": {
            "capacity_pct": _simulate_capacity(volume_multiplier, failure_mult=8),
        },
        "settlement_engine": {
            "capacity_pct": _simulate_capacity(volume_multiplier, failure_mult=6),
        },
        "risk_engine": {
            "capacity_pct": _simulate_capacity(volume_multiplier, failure_mult=6),
        },
        "eks_pods": {
            "capacity_pct": _simulate_capacity(volume_multiplier, failure_mult=7),
        }
    }
    return base


def _simulate_kafka_lag(volume_multiplier: float) -> float:
    base_lag = 500
    lag = base_lag * (volume_multiplier ** 1.4)
    noise = random.uniform(0.85, 1.15)
    return round(lag * noise)


def _simulate_capacity(volume_multiplier: float, failure_mult: float) -> float:
    pct = (volume_multiplier / failure_mult) * 100
    noise = random.uniform(-5, 5)
    return round(min(pct + noise, 105), 1)


def run_live_analysis(event_id: str, volume_multiplier: float,
                      metrics: dict = None) -> dict:
    if metrics is None:
        metrics = generate_live_metrics(volume_multiplier)

    thresholds = get_adaptive_thresholds(volume_multiplier)
    triage = triage_systems(metrics, volume_multiplier)
    confidence = get_confidence_decay(volume_multiplier)

    classifications = []
    for sys_name, sys_metrics in metrics.items():
        for metric_name, metric_value in sys_metrics.items():
            classification = distinguish_surge_vs_failure(
                sys_name, metric_value, metric_name, volume_multiplier
            )
            classifications.append(classification)
            log_surge_metric(
                event_id=event_id,
                phase="live",
                volume=volume_multiplier,
                system=sys_name,
                metric=metric_name,
                value=metric_value,
                threshold=thresholds.get("kafka_lag_threshold", 0),
                status=classification["status"],
                notes=classification["classification"]
            )

    genuine_failures = [
        c for c in classifications
        if c["classification"] == "genuine_failure"
    ]

    llm_summary = None
    if genuine_failures:
        llm_summary = _get_llm_situational_summary(
            volume_multiplier, triage, genuine_failures
        )

    overall_status = _calculate_overall_status(triage)

    return {
        "event_id": event_id,
        "volume_multiplier": volume_multiplier,
        "volume_band": thresholds["volume_band"],
        "thresholds": thresholds,
        "metrics": metrics,
        "triage": triage,
        "classifications": classifications,
        "genuine_failures": genuine_failures,
        "overall_status": overall_status,
        "confidence": confidence,
        "llm_summary": llm_summary,
        "phase": "live"
    }


def _get_llm_situational_summary(volume_multiplier: float,
                                  triage: list, failures: list) -> dict:
    top_triage = triage[:3]

    prompt = f"""
Current IPO surge situation:
Volume: {volume_multiplier:.0f}x normal
Genuine failures detected: {len(failures)}

Top priority issues:
{[{'system': t['display_name'], 'status': t['status'], 'action': t['action']} for t in top_triage]}

Provide a 2-sentence plain-English situational update for the ops team.

Return JSON:
{{
  "situation": "plain English 2-sentence summary",
  "immediate_action": "single most important thing to do right now",
  "estimated_stabilisation_minutes": 5
}}
"""
    result = query_mistral_json(prompt, SYSTEM_LIVE_SURGE)
    if "error" in result:
        return {
            "situation": f"Surge at {volume_multiplier:.0f}x with {len(failures)} genuine failures detected. Triage list active.",
            "immediate_action": top_triage[0]["action"] if top_triage else "Review all systems",
            "estimated_stabilisation_minutes": 15
        }
    return result


def _calculate_overall_status(triage: list) -> str:
    if not triage:
        return "stable"
    critical = sum(1 for t in triage if t["status"] == "critical")
    warnings = sum(1 for t in triage if t["status"] == "warning")
    if critical >= 2:
        return "critical"
    elif critical >= 1:
        return "high"
    elif warnings >= 2:
        return "elevated"
    elif warnings >= 1:
        return "watch"
    return "stable"
