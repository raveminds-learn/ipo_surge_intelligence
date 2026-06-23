import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.threshold_adapter import (
    get_volume_band, get_adaptive_thresholds,
    evaluate_system_health, get_confidence_decay
)
from core.surge_simulator import (
    simulate_system_at_volume, run_full_simulation, generate_readiness_score
)
from core.triage_engine import triage_systems, distinguish_surge_vs_failure


def test_volume_bands():
    assert get_volume_band(2) == "normal"
    assert get_volume_band(10) == "elevated"
    assert get_volume_band(20) == "high"
    assert get_volume_band(40) == "surge"
    assert get_volume_band(70) == "critical"
    print("✅ test_volume_bands passed")


def test_adaptive_thresholds():
    t_normal = get_adaptive_thresholds(2)
    t_surge = get_adaptive_thresholds(40)
    assert t_surge["kafka_lag_threshold"] > t_normal["kafka_lag_threshold"]
    assert t_surge["latency_threshold_ms"] > t_normal["latency_threshold_ms"]
    print("✅ test_adaptive_thresholds passed — thresholds scale with volume")


def test_confidence_decay():
    assert get_confidence_decay(10) == 1.0
    assert get_confidence_decay(67) == 1.0
    assert get_confidence_decay(100) < 1.0
    assert get_confidence_decay(200) >= 0.3
    print("✅ test_confidence_decay passed")


def test_system_simulation():
    result = simulate_system_at_volume("order_gateway", 5)
    assert result["status"] == "stable"
    result_high = simulate_system_at_volume("order_gateway", 100)
    assert result_high["status"] == "failure"
    print("✅ test_system_simulation passed")


def test_full_simulation():
    sim = run_full_simulation("TestCo")
    assert "10x" in sim["scenarios"]
    assert "50x" in sim["scenarios"]
    assert "100x" in sim["scenarios"]
    assert sim["scenarios"]["10x"]["overall_status"] in ["stable", "elevated", "warning", "critical"]
    print("✅ test_full_simulation passed")


def test_triage():
    metrics = {
        "kafka_consumer": {"kafka_lag": 45000},
        "order_gateway": {"capacity_pct": 95}
    }
    triage = triage_systems(metrics, volume_multiplier=40)
    assert len(triage) > 0
    assert triage[0]["priority_rank"] == 1
    print("✅ test_triage passed")


def test_surge_vs_failure():
    result_expected = distinguish_surge_vs_failure(
        "kafka_consumer", 5000, "kafka_lag", 40
    )
    result_failure = distinguish_surge_vs_failure(
        "kafka_consumer", 80000, "kafka_lag", 5
    )
    assert result_expected["classification"] in ["expected_surge_behaviour", "genuine_failure", "investigate"]
    assert result_failure["classification"] in ["genuine_failure", "investigate"]
    print("✅ test_surge_vs_failure passed")


if __name__ == "__main__":
    print("RaveMinds — IPO Surge Intelligence Agent Tests\n")
    test_volume_bands()
    test_adaptive_thresholds()
    test_confidence_decay()
    test_system_simulation()
    test_full_simulation()
    test_triage()
    test_surge_vs_failure()
    print("\n✅ All tests passed")
