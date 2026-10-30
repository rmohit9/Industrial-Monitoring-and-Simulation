
import numpy as np
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models import Sensor, Telemetry, Pump, Tank


def generate_telemetry(
    session: Session,
    readings_per_sensor: int = 1000,
    seed: int = 20261022,
):
    rng = np.random.default_rng(seed)

    sensors = session.scalars(
        select(Sensor).order_by(Sensor.id)
    ).all()

    if not sensors:
        raise ValueError("No sensors found. Generate sensors first.")

    pumps = {
        p.equipment_id: p
        for p in session.scalars(select(Pump)).all()
    }
    tanks = {
        t.equipment_id: t
        for t in session.scalars(select(Tank)).all()
    }

    start_time = datetime(2026, 1, 1, 0, 0, 0)
    batch_size = 5000
    batch = []
    inserted = 0

    for sensor in sensors:
        # Check whether this sensor already has telemetry.
        existing = session.scalar(
            select(Telemetry.id)
            .where(Telemetry.sensor_id == sensor.id)
            .limit(1)
        )

        if existing is not None:
            print(f"Skipping {sensor.id}: telemetry already exists")
            continue

        pump = pumps.get(sensor.equipment_id)
        tank = tanks.get(sensor.equipment_id)

        for i in range(readings_per_sensor):
            timestamp = start_time + timedelta(minutes=i)

            if sensor.sensor_type == "flow":
                baseline = pump.rated_flow if pump else 100.0
                value = max(0.0, rng.normal(baseline, baseline * 0.03))

            elif sensor.sensor_type == "pressure":
                baseline = (
                    pump.shutoff_head * 9.81
                    if pump
                    else 300.0
                )
                value = max(0.0, rng.normal(baseline, baseline * 0.02))

            elif sensor.sensor_type == "level":
                baseline = tank.initial_level if tank else 300.0
                value = np.clip(
                    baseline + rng.normal(0, tank.capacity * 0.005),
                    0,
                    tank.capacity,
                )

            else:
                continue

            batch.append(
                {
                    "sensor_id": sensor.id,
                    "timestamp": timestamp,
                    "value": round(float(value), 4),
                    "quality_status": "good",
                }
            )

            if len(batch) >= batch_size:
                session.execute(Telemetry.__table__.insert(), batch)
                inserted += len(batch)
                batch.clear()

    if batch:
        session.execute(Telemetry.__table__.insert(), batch)
        inserted += len(batch)

    session.commit()

    print(f"Telemetry records inserted: {inserted}")
    print(f"Expected total for a fresh dataset: "
          f"{len(sensors) * readings_per_sensor:,}")
