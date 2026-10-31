
import numpy as np

from src.detection.rule_engine import THRESHOLDS

SEED = 20261022
BASELINE = 100.0
NORMAL_READINGS = 1000


def detect_anomaly(baseline, observed, threshold):
    if baseline == 0:
        deviation = 0.0 if observed == 0 else 100.0
    else:
        deviation = abs(observed - baseline) / abs(baseline) * 100

    return deviation >= threshold


def test_production_thresholds():
    rng = np.random.default_rng(SEED)

    for sensor_type, threshold in THRESHOLDS.items():
        normal = BASELINE + rng.normal(0, 3, NORMAL_READINGS)
        subtle_faults = BASELINE * 1.10 + rng.normal(0, 1, 100)
        severe_faults = BASELINE * 1.30 + rng.normal(0, 2, 100)

        false_positives = sum(
            detect_anomaly(BASELINE, value, threshold)
            for value in normal
        )
        subtle_detected = sum(
            detect_anomaly(BASELINE, value, threshold)
            for value in subtle_faults
        )
        severe_detected = sum(
            detect_anomaly(BASELINE, value, threshold)
            for value in severe_faults
        )

        print(f"\nSensor type: {sensor_type}")
        print(f"Threshold: {threshold:.1f}%")
        print(f"Normal false positives: {false_positives}/{NORMAL_READINGS}")
        print(f"Subtle faults detected: {subtle_detected}/100")
        print(f"Severe faults detected: {severe_detected}/100")

        assert false_positives <= 20, (
            f"{sensor_type}: too many normal false positives"
        )
        assert subtle_detected >= 90, (
            f"{sensor_type}: too few subtle faults detected"
        )
        assert severe_detected >= 95, (
            f"{sensor_type}: too few severe faults detected"
        )
