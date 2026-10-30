
import random
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models import Equipment, Facility, ScenarioEvent


SCENARIO_TYPES = [
    "leak",
    "blockage",
    "pump_degradation",
    "sensor_fault",
]

SEVERITIES = ["low", "medium", "high"]


def generate_scenarios(
    session: Session,
    number_of_scenarios: int = 12,
    seed: int = 20261022,
):
    """Create reproducible fault-event records."""

    rng = random.Random(seed)

    facilities = session.scalars(
        select(Facility).order_by(Facility.id)
    ).all()

    if not facilities:
        raise ValueError("No facilities found. Generate master data first.")

    equipment = session.scalars(
        select(Equipment).order_by(Equipment.id)
    ).all()

    if not equipment:
        raise ValueError("No equipment found.")

    existing_ids = set(
        session.scalars(select(ScenarioEvent.id)).all()
    )

    created = 0
    start_time = datetime(2026, 1, 1, 0, 0, 0)

    for i in range(1, number_of_scenarios + 1):
        event_id = f"EVT-{i:06d}"

        # Do not duplicate an event if this function is run again.
        if event_id in existing_ids:
            continue

        scenario_type = SCENARIO_TYPES[(i - 1) % len(SCENARIO_TYPES)]

        if scenario_type == "pump_degradation":
            candidates = [
                item for item in equipment
                if item.equipment_type == "pump"
            ]
        elif scenario_type == "blockage":
            candidates = [
                item for item in equipment
                if item.equipment_type in ("valve", "pipe")
            ]
        elif scenario_type == "sensor_fault":
            candidates = [
                item for item in equipment
                if item.equipment_type in ("pump", "tank", "valve")
            ]
        else:
            candidates = [
                item for item in equipment
                if item.equipment_type in ("pipe", "tank")
            ]

        # Pipe is a separate entity, not an Equipment subtype.
        # For now, select equipment for all events.
        if not candidates:
            candidates = equipment

        affected = rng.choice(candidates)
        facility_id = affected.facility_id

        event_start = start_time + timedelta(
            minutes=rng.randint(0, 500)
        )
        duration_minutes = rng.randint(15, 120)

        session.add(
            ScenarioEvent(
                id=event_id,
                facility_id=facility_id,
                equipment_id=affected.id,
                scenario_type=scenario_type,
                start_time=event_start,
                end_time=event_start + timedelta(
                    minutes=duration_minutes
                ),
                severity=rng.choice(SEVERITIES),
                description=(
                    f"Simulated {scenario_type.replace('_', ' ')} "
                    f"affecting {affected.id}"
                ),
                status="planned",
            )
        )

        created += 1

    session.flush()
    print(f"Scenario events created: {created}")
