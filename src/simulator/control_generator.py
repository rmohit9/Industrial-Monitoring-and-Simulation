
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database import SessionLocal
from src.models import (
    Facility,
    Pump,
    Sensor,
    ScenarioEvent,
    SimulatedTelemetry,
    Tank,
    Telemetry,
)


def generate_controls(session: Session, sample_every: int = 10):
    if sample_every < 1:
        raise ValueError("sample_every must be at least 1.")

    sensors = session.scalars(
        select(Sensor).order_by(Sensor.id)
    ).all()

    if not sensors:
        raise ValueError("No sensors found.")

    facilities = {
        f.id: f
        for f in session.scalars(select(Facility)).all()
    }
    pumps = {
        p.equipment_id: p
        for p in session.scalars(select(Pump)).all()
    }
    tanks = {
        t.equipment_id: t
        for t in session.scalars(select(Tank)).all()
    }

    existing_events = {
        event.id: event
        for event in session.scalars(
            select(ScenarioEvent).where(
                ScenarioEvent.id.like("CTRL-2026-%")
            )
        ).all()
    }

    # Use the full telemetry time range for control events.
    all_readings = session.scalars(
        select(Telemetry).order_by(Telemetry.timestamp)
    ).all()

    if not all_readings:
        raise ValueError("No baseline telemetry found.")

    start_time = all_readings[0].timestamp
    end_time = all_readings[-1].timestamp

    for facility_id in sorted(facilities):
        event_id = f"CTRL-2026-{facility_id}"

        if event_id not in existing_events:
            session.add(
                ScenarioEvent(
                    id=event_id,
                    facility_id=facility_id,
                    equipment_id=None,
                    pipe_id=None,
                    sensor_id=None,
                    scenario_type="normal_control",
                    start_time=start_time,
                    end_time=end_time,
                    severity="low",
                    description=(
                        "Normal baseline readings used as "
                        "control samples for evaluation."
                    ),
                    status="control",
                )
            )

    session.flush()

    existing_keys = {
        (event_id, sensor_id, timestamp)
        for event_id, sensor_id, timestamp in session.execute(
            select(
                SimulatedTelemetry.event_id,
                SimulatedTelemetry.sensor_id,
                SimulatedTelemetry.timestamp,
            )
        ).all()
    }

    inserted = 0

    for sensor in sensors:
        control_event_id = f"CTRL-2026-{sensor.facility_id}"

        if sensor.sensor_type == "flow":
            pump = pumps.get(sensor.equipment_id)
            if pump is None:
                continue
            nominal = pump.rated_flow

        elif sensor.sensor_type == "pressure":
            pump = pumps.get(sensor.equipment_id)
            nominal = (
                pump.shutoff_head * 9.81
                if pump is not None
                else 300.0
            )

        elif sensor.sensor_type == "level":
            tank = tanks.get(sensor.equipment_id)
            if tank is None:
                continue
            nominal = tank.initial_level

        else:
            continue

        readings = session.scalars(
            select(Telemetry)
            .where(Telemetry.sensor_id == sensor.id)
            .order_by(Telemetry.timestamp)
        ).all()

        for index, reading in enumerate(readings):
            if index % sample_every != 0:
                continue

            key = (
                control_event_id,
                sensor.id,
                reading.timestamp,
            )

            if key in existing_keys:
                continue


            session.add(
                SimulatedTelemetry(
                    event_id=control_event_id,
                    sensor_id=sensor.id,
                    timestamp=reading.timestamp,
                    baseline_value=round(float(reading.value), 4),
                    simulated_value=round(float(reading.value), 4),
                )
            )

            existing_keys.add(key)
            inserted += 1

    session.flush()
    print(f"Normal control readings added: {inserted}")


def main():
    with SessionLocal() as session:
        try:
            generate_controls(session)
            session.commit()
            print("Normal control generation completed.")
        except Exception:
            session.rollback()
            raise


if __name__ == "__main__":
    main()
