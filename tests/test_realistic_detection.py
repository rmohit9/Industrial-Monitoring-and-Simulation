
import numpy as np


THRESHOLD_PCT = 8.0
SEED = 20261022


def detect_anomaly(baseline, observed):
    if baseline == 0:
        deviation_pct = 0.0 if observed == 0 else 100.0
    else:
        deviation_pct = abs(observed - baseline) / abs(baseline) * 100

    return deviation_pct >= THRESHOLD_PCT


def test_realistic_detection():
    rng = np.random.default_rng(SEED)

    baseline = 100.0

    # Normal readings: small random fluctuations
    normal_readings = baseline + rng.normal(0, 3, 1000)

    # Subtle faults: 10% change, below threshold
    subtle_faults = baseline * 1.10 + rng.normal(0, 1, 100)

    # Severe faults: 30% change
    severe_faults = baseline * 1.30 + rng.normal(0, 2, 100)

    normal_predictions = [
        detect_anomaly(baseline, value)
        for value in normal_readings
    ]

    subtle_predictions = [
        detect_anomaly(baseline, value)
        for value in subtle_faults
    ]

    severe_predictions = [
        detect_anomaly(baseline, value)
        for value in severe_faults
    ]

    normal_false_positives = sum(normal_predictions)
    subtle_detected = sum(subtle_predictions)
    severe_detected = sum(severe_predictions)

    print("\nREALISTIC DETECTION TEST")
    print("-----------------------")
    print(f"Normal readings: {len(normal_readings)}")
    print(f"Normal false positives: {normal_false_positives}")
    print(f"Subtle faults detected: {subtle_detected}/{len(subtle_faults)}")
    print(f"Severe faults detected: {severe_detected}/{len(severe_faults)}")

    assert normal_false_positives <= 20
    assert subtle_detected >= 90
    assert severe_detected >= 95


if __name__ == "__main__":
    test_realistic_detection()
