
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models import (
    DetectionResult,
    Equipment,
    Pump,
    Sensor,
    SimulatedTelemetry,
    Tank,
)

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
        raise ValueError("No simulated or control readings found.")

    sensors = {
        s.id: s
        for s in session.scalars(select(Sensor)).all()
    }
    equipment = {
        e.id: e
        for e in session.scalars(select(Equipment)).all()
    }
    pumps = {
        p.equipment_id: p
        for p in session.scalars(select(Pump)).all()
    }
    tanks = {
        t.equipment_id: t
        for t in session.scalars(select(Tank)).all()
    }

    existing = {
        (r.event_id, r.sensor_id, r.timestamp): r
        for r in session.scalars(select(DetectionResult)).all()
    }

    inserted = 0
    updated = 0
    anomalies = 0

    for reading in readings:
        sensor = sensors.get(reading.sensor_id)
        if sensor is None:
            continue

        # Use a consistent nominal reference for every sample.
        if sensor.sensor_type == "flow":
            pump = pumps.get(sensor.equipment_id)
            if pump is None:
                continue
            reference = pump.rated_flow

        elif sensor.sensor_type == "pressure":
            pump = pumps.get(sensor.equipment_id)
            reference = (
                pump.shutoff_head * 9.81
                if pump is not None
                else 300.0
            )

        elif sensor.sensor_type == "level":
            tank = tanks.get(sensor.equipment_id)
            if tank is None:
                continue
            reference = tank.initial_level

        else:
            continue


        # Compare each reading against its recorded baseline.
        if sensor.sensor_type not in THRESHOLDS:
            continue

        reference = reading.baseline_value
        observed = reading.simulated_value
        threshold = THRESHOLDS[sensor.sensor_type]


        if reference == 0:
            deviation = 0.0 if observed == 0 else 100.0
        else:
            deviation = abs(observed - reference) / abs(reference) * 100

        is_anomaly = deviation >= threshold
        result = "anomaly" if is_anomaly else "normal"

        if is_anomaly:
            anomalies += 1

        explanation = (
            f"Observed value differs from nominal reference by "
            f"{deviation:.2f}%; threshold is {threshold:.2f}%."
        )

        key = (
            reading.event_id,
            reading.sensor_id,
            reading.timestamp,
        )
        record = existing.get(key)

        values = {
            "baseline_value": round(float(reference), 4),
            "observed_value": round(float(observed), 4),
            "deviation_pct": round(float(deviation), 4),
            "threshold_pct": threshold,
            "result": result,
            "explanation": explanation,
        }

        if record is None:
            session.add(
                DetectionResult(
                    event_id=reading.event_id,
                    sensor_id=reading.sensor_id,
                    timestamp=reading.timestamp,
                    **values,
                )
            )
            inserted += 1
        else:
            for field, value in values.items():
                setattr(record, field, value)
            updated += 1

    session.flush()

    print(f"New results: {inserted}")
    print(f"Existing results recalculated: {updated}")
    print(f"Anomalies detected: {anomalies}")


if __name__ == "__main__":
    from src.database import SessionLocal

    with SessionLocal() as session:
        try:
            detect_anomalies(session)
            session.commit()
        except Exception:
            session.rollback()
            raise
