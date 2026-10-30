
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models import (
    DetectionResult,
    Sensor,
    SimulatedTelemetry,
)


# Initial thresholds for this synthetic dataset.
THRESHOLDS = {
    "flow": 15.0,
    "pressure": 15.0,
    "level": 0.5,
}


def detect_anomalies(session: Session):
    readings = session.scalars(
        select(SimulatedTelemetry).order_by(
            SimulatedTelemetry.event_id,
            SimulatedTelemetry.sensor_id,
            SimulatedTelemetry.timestamp,
        )
    ).all()

    if not readings:
        raise ValueError(
            "No simulated readings found. "
            "Run python run_fault_simulation.py first."
        )

    sensors = {
        sensor.id: sensor
        for sensor in session.scalars(select(Sensor)).all()
    }

    existing_keys = set(
        session.execute(
            select(
                DetectionResult.event_id,
                DetectionResult.sensor_id,
                DetectionResult.timestamp,
            )
        ).all()
    )

    inserted = 0
    anomaly_count = 0
    skipped = 0

    for reading in readings:
        key = (
            reading.event_id,
            reading.sensor_id,
            reading.timestamp,
        )

        if key in existing_keys:
            skipped += 1
            continue

        sensor = sensors.get(reading.sensor_id)

        if sensor is None:
            continue

        threshold = THRESHOLDS.get(sensor.sensor_type)

        if threshold is None:
            continue

        baseline = reading.baseline_value
        observed = reading.simulated_value

        # Percentage change relative to the baseline.
        if baseline == 0:
            deviation_pct = (
                0.0 if observed == 0 else 100.0
            )
        else:
            deviation_pct = (
                abs(observed - baseline)
                / abs(baseline)
                * 100.0
            )

        is_anomaly = deviation_pct >= threshold

        if is_anomaly:
            result = "anomaly"
            explanation = (
                f"{sensor.sensor_type} changed by "
                f"{deviation_pct:.2f}%; "
                f"threshold is {threshold:.2f}%."
            )
            anomaly_count += 1
        else:
            result = "normal"
            explanation = (
                f"Change of {deviation_pct:.2f}% "
                f"is below the {threshold:.2f}% threshold."
            )

        session.add(
            DetectionResult(
                event_id=reading.event_id,
                sensor_id=reading.sensor_id,
                timestamp=reading.timestamp,
                baseline_value=baseline,
                observed_value=observed,
                deviation_pct=round(deviation_pct, 4),
                threshold_pct=threshold,
                result=result,
                explanation=explanation,
            )
        )

        inserted += 1

    session.flush()

    print(f"Detection results saved: {inserted}")
    print(f"Anomalies detected: {anomaly_count}")
    print(f"Existing results skipped: {skipped}")
