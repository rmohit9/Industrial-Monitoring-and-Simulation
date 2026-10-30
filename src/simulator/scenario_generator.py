
import random
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models import (
    Equipment,
    Facility,
    Pipe,
    ScenarioEvent,
    Sensor,
)


def generate_scenarios(
    session: Session,
    number_of_scenarios: int = 12,
    seed: int = 20261022,
):
    rng = random.Random(seed)

    facilities = session.scalars(
        select(Facility).order_by(Facility.id)
    ).all()

    if not facilities:
        raise ValueError("No facilities found.")

    pumps = session.scalars(
        select(Equipment)
        .where(Equipment.equipment_type == "pump")
        .order_by(Equipment.id)
    ).all()

    pipes = session.scalars(
        select(Pipe).order_by(Pipe.id)
    ).all()

    sensors = session.scalars(
        select(Sensor).order_by(Sensor.id)
    ).all()

    if not pumps or not pipes or not sensors:
        raise ValueError(
            "Missing pumps, pipes, or sensors. "
            "Generate master data first."
        )

    existing_ids = set(
        session.scalars(select(ScenarioEvent.id)).all()
    )

    scenario_types = [
        "leak",
        "blockage",
        "pump_degradation",
        "sensor_fault",
    ]

    severities = ["low", "medium", "high"]
    start_time = datetime(2026, 1, 1)

    created = 0

    for i in range(1, number_of_scenarios + 1):
        event_id = f"EVT-2026-{i:06d}"

        if event_id in existing_ids:
            continue

        scenario_type = scenario_types[(i - 1) % 4]

        equipment_id = None
        pipe_id = None
        sensor_id = None

        if scenario_type in ("leak", "blockage"):
            candidates = pipes
            asset = rng.choice(candidates)
            pipe_id = asset.id
            facility_id = asset.facility_id

        elif scenario_type == "pump_degradation":
            asset = rng.choice(pumps)
            equipment_id = asset.id
            facility_id = asset.facility_id

        else:
            asset = rng.choice(sensors)
            sensor_id = asset.id
            equipment_id = asset.equipment_id
            facility_id = asset.facility_id

        event_start = start_time + timedelta(
            minutes=rng.randint(0, 500)
        )

        event_end = event_start + timedelta(
            minutes=rng.randint(15, 120)
        )

        session.add(
            ScenarioEvent(
                id=event_id,
                facility_id=facility_id,
                equipment_id=equipment_id,
                pipe_id=pipe_id,
                sensor_id=sensor_id,
                scenario_type=scenario_type,
                start_time=event_start,
                end_time=event_end,
                severity=rng.choice(severities),
                description=(
                    f"Simulated {scenario_type.replace('_', ' ')}"
                ),
                status="planned",
            )
        )

        created += 1

    session.flush()
    print(f"New scenario events created: {created}")
