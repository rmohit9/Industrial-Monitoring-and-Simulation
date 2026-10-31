
from sqlalchemy import select

from src.database import SessionLocal
from src.models import ScenarioEvent, SimulatedTelemetry, Sensor


def update_leak_simulations():
    with SessionLocal() as session:
        rows = session.execute(
            select(
                SimulatedTelemetry,
                Sensor.sensor_type,
            )
            .join(
                ScenarioEvent,
                SimulatedTelemetry.event_id == ScenarioEvent.id,
            )
            .join(
                Sensor,
                SimulatedTelemetry.sensor_id == Sensor.id,
            )
            .where(ScenarioEvent.scenario_type == "leak")
        ).all()

        updated = 0

        for reading, sensor_type in rows:
            baseline = float(reading.baseline_value)

            if sensor_type in ("flow", "level"):
                reading.simulated_value = round(
                    max(0.0, baseline * 0.65), 4
                )
                updated += 1

        session.commit()

    print(f"Leak readings updated: {updated}")


if __name__ == "__main__":
    update_leak_simulations()
