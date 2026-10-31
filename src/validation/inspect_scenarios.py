
from collections import Counter

from sqlalchemy import select

from src.database import SessionLocal
from src.models import ScenarioEvent, SimulatedTelemetry


def inspect_scenarios():
    with SessionLocal() as session:
        events = session.scalars(
            select(ScenarioEvent)
        ).all()

        readings = session.execute(
            select(
                ScenarioEvent.scenario_type,
                SimulatedTelemetry.event_id,
                SimulatedTelemetry.sensor_id,
            )
            .join(
                ScenarioEvent,
                ScenarioEvent.id == SimulatedTelemetry.event_id,
            )
        ).all()

    event_counts = Counter(
        event.scenario_type for event in events
    )
    reading_counts = Counter(
        row[0] for row in readings
    )

    print("\nSCENARIO EVENT COUNTS")
    print("---------------------")
    for scenario, count in sorted(event_counts.items()):
        print(f"{scenario}: {count}")

    print("\nSIMULATED TELEMETRY COUNTS")
    print("--------------------------")
    for scenario, count in sorted(reading_counts.items()):
        print(f"{scenario}: {count}")

    print(f"\nTotal events: {len(events)}")
    print(f"Total simulated readings: {len(readings)}")


if __name__ == "__main__":
    inspect_scenarios()
