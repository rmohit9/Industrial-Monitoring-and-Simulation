
from sqlalchemy import and_, select

from src.database import SessionLocal
from src.models import (
    DetectionResult,
    ScenarioEvent,
    SimulatedTelemetry,
)


def inspect_missed_leaks():
    with SessionLocal() as session:
        rows = session.execute(
            select(
                SimulatedTelemetry.sensor_id,
                SimulatedTelemetry.timestamp,
                SimulatedTelemetry.baseline_value,
                SimulatedTelemetry.simulated_value,
                DetectionResult.deviation_pct,
                DetectionResult.threshold_pct,
            )
            .join(
                ScenarioEvent,
                ScenarioEvent.id == SimulatedTelemetry.event_id,
            )
            .outerjoin(
                DetectionResult,
                and_(
                    DetectionResult.event_id
                    == SimulatedTelemetry.event_id,
                    DetectionResult.sensor_id
                    == SimulatedTelemetry.sensor_id,
                    DetectionResult.timestamp
                    == SimulatedTelemetry.timestamp,
                ),
            )
            .where(ScenarioEvent.scenario_type == "leak")
            .order_by(DetectionResult.deviation_pct)
        ).all()

    missed = [
        row for row in rows
        if row[4] is None or row[4] < row[5]
    ]

    print("\nMISSED LEAK READINGS")
    print("--------------------")
    print(f"Total leak readings: {len(rows)}")
    print(f"Missed leak readings: {len(missed)}")

    for sensor_id, timestamp, baseline, observed, deviation, threshold in missed[:20]:
        print(
            f"sensor={sensor_id}, time={timestamp}, "
            f"baseline={baseline}, observed={observed}, "
            f"deviation={deviation}%, threshold={threshold}%"
        )


if __name__ == "__main__":
    inspect_missed_leaks()
