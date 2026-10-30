
from sqlalchemy import select

from src.database import SessionLocal
from src.models import SimulatedTelemetry, Telemetry


def fix_control_baselines():
    with SessionLocal() as session:
        rows = session.execute(
            select(SimulatedTelemetry, Telemetry.value)
            .join(
                Telemetry,
                (Telemetry.sensor_id == SimulatedTelemetry.sensor_id)
                & (Telemetry.timestamp == SimulatedTelemetry.timestamp),
            )
            .where(
                SimulatedTelemetry.event_id.like("CTRL-2026-%")
            )
        ).all()

        updated = 0

        for simulated_reading, original_value in rows:
            simulated_reading.baseline_value = float(original_value)
            simulated_reading.simulated_value = float(original_value)
            updated += 1

        session.commit()

        print(f"Control readings corrected: {updated}")


if __name__ == "__main__":
    fix_control_baselines()
