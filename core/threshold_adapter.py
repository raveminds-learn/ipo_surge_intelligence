import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
BASELINES_PATH = str(BASE_DIR / "data" / "system_baselines.json")

with open(BASELINES_PATH) as f:
    BASELINES = json.load(f)

VOLUME_BANDS = BASELINES["adaptive_thresholds"]["volume_bands"]
SYSTEMS = BASELINES["systems"]


def get_volume_band(volume_multiplier: float) -> str:
    for band, config in VOLUME_BANDS.items():
        if config["min"] <= volume_multiplier < config["max"]:
            return band
    return "critical"


def get_adaptive_thresholds(volume_multiplier: float) -> dict:
    band = get_volume_band(volume_multiplier)
    config = VOLUME_BANDS[band]
    return {
        "volume_band": band,
        "volume_multiplier": volume_multiplier,
        "kafka_lag_threshold": config["lag_threshold"],
        "latency_threshold_ms": config["latency_threshold_ms"],
        "description": f"Thresholds adapted for {band} volume ({volume_multiplier:.1f}x normal)"
    }


def evaluate_system_health(system_name: str, current_value: float,
                            metric: str, volume_multiplier: float) -> dict:
    thresholds = get_adaptive_thresholds(volume_multiplier)
    band = thresholds["volume_band"]
    system = SYSTEMS.get(system_name, {})

    if metric == "kafka_lag":
        threshold = thresholds["kafka_lag_threshold"]
        critical = threshold * 2
        pct = min(current_value / critical * 100, 100) if critical > 0 else 0
        if current_value >= critical:
            status = "critical"
        elif current_value >= threshold:
            status = "warning"
        else:
            status = "healthy"
        return {
            "system": system_name, "metric": metric,
            "current": current_value, "threshold": threshold,
            "critical": critical, "status": status,
            "pct_capacity": round(pct, 1),
            "volume_band": band,
            "adapted": True
        }

    if metric == "capacity_pct":
        failure_mult = system.get("failure_threshold_multiplier", 8)
        effective_capacity = system.get("normal_capacity_rps", 1000) * failure_mult
        actual_capacity = system.get("max_capacity_rps", 8000)
        surge_capacity = min(effective_capacity, actual_capacity)
        threshold_pct = 75 + ({"normal": 0, "elevated": 5, "high": 10,
                                "surge": 15, "critical": 20}.get(band, 0))
        if current_value >= 95:
            status = "critical"
        elif current_value >= threshold_pct:
            status = "warning"
        else:
            status = "healthy"
        return {
            "system": system_name, "metric": metric,
            "current": current_value, "threshold": threshold_pct,
            "status": status, "volume_band": band, "adapted": True
        }

    return {
        "system": system_name, "metric": metric,
        "current": current_value, "threshold": None,
        "status": "unknown", "volume_band": band, "adapted": False
    }


def get_confidence_decay(volume_multiplier: float, max_historical_volume: float = 67) -> float:
    if volume_multiplier <= max_historical_volume:
        return 1.0
    excess = volume_multiplier - max_historical_volume
    decay = max(0.3, 1.0 - (excess / max_historical_volume) * 0.5)
    return round(decay, 2)
