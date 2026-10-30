
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models import (
    Equipment,
    Pipe,
    ScenarioEvent,
    Sensor,
    SimulatedTelemetry,
    Telemetry,
)


def simulate_faults(session: Session):
    # Process only events created by the corrected generator.
    events = session.scalars(
        select(ScenarioEvent)
        .where(
            ScenarioEvent.id.like("EVT-2026-%"),
            ScenarioEvent.status == "planned",
        )
        .order_by(ScenarioEvent.id)
    ).all()

    if not events:
        raise ValueError(
            "No planned EVT-2026 events found. "
            "Run generate_scenarios.py first."
        )

    sensors = session.scalars(
        select(Sensor).order_by(Sensor.id)
    ).all()

    equipment = {
        item.id: item
        for item in session.scalars(select(Equipment)).all()
    }

    pipes = {
        item.id: item
        for item in session.scalars(select(Pipe)).all()
    }

    created = 0
    skipped = 0

    for event in events:
        # Determine which sensors may observe this event.
        if event.scenario_type == "sensor_fault":
            affected_sensors = [
                s for s in sensors if s.id == event.sensor_id
            ]

        elif event.scenario_type == "pump_degradation":
            affected_sensors = [
                s for s in sensors
                if s.equipment_id == event.equipment_id
                and s.sensor_type in ("flow", "pressure")
            ]

        elif event.scenario_type in ("leak", "blockage"):
            pipe = pipes.get(event.pipe_id)

            if pipe is None:
                print(
                    f"Skipping {event.id}: valid pipe not found."
                )
                skipped += 1
                continue

            endpoint_ids = {
                pipe.source_equipment_id,
                pipe.target_equipment_id,
            }

            if event.scenario_type == "leak":
                allowed_types = ("flow", "level")
            else:
                allowed_types = ("flow", "pressure")

            affected_sensors = [
                s for s in sensors
                if s.equipment_id in endpoint_ids
                and s.sensor_type in allowed_types
            ]

        else:
            skipped += 1
            continue

        for sensor in affected_sensors:
            readings = session.scalars(
                select(Telemetry)
                .where(
                    Telemetry.sensor_id == sensor.id,
                    Telemetry.timestamp >= event.start_time,
                    Telemetry.timestamp <= event.end_time,
                )
                .order_by(Telemetry.timestamp)
            ).all()

            for reading in readings:
                # Avoid duplicate output if rerun.
                exists = session.scalar(
                    select(SimulatedTelemetry.id).where(
                        SimulatedTelemetry.event_id == event.id,
                        SimulatedTelemetry.sensor_id == sensor.id,
                        SimulatedTelemetry.timestamp == reading.timestamp,
                    ).limit(1)
                )

                if exists is not None:
                    continue

                baseline = reading.value
                simulated = baseline

                if event.scenario_type == "leak":
                    if sensor.sensor_type == "flow":
                        simulated = baseline * 0.65
                    elif sensor.sensor_type == "level":
                        simulated = max(0.0, baseline - 5.0)

                elif event.scenario_type == "blockage":
                    if sensor.sensor_type == "flow":
                        simulated = baseline * 0.45
                    elif sensor.sensor_type == "pressure":
                        simulated = baseline * 1.25

                elif event.scenario_type == "pump_degradation":
                    if sensor.sensor_type == "flow":
                        simulated = baseline * 0.70
                    elif sensor.sensor_type == "pressure":
                        simulated = baseline * 0.80

                elif event.scenario_type == "sensor_fault":
                    # A synthetic sensor fault: a 40% high bias.
                    simulated = baseline * 1.40

                session.add(
                    SimulatedTelemetry(
                        event_id=event.id,
                        sensor_id=sensor.id,
                        timestamp=reading.timestamp,
                        baseline_value=round(baseline, 4),
                        simulated_value=round(
                            max(0.0, simulated), 4
                        ),
                    )
                )
                created += 1

    session.flush()

    print(f"Simulated readings created: {created}")
    print(f"Events skipped: {skipped}")
