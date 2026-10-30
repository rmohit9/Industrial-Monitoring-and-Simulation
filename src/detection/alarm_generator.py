
from sqlalchemy import select

from src.database import SessionLocal
from src.models import Alarm, DetectionResult, Sensor


def generate_alarms():
    with SessionLocal() as session:
        results = session.scalars(
            select(DetectionResult)
            .where(DetectionResult.result == "anomaly")
            .order_by(DetectionResult.id)
        ).all()

        existing_ids = set(
            session.scalars(
                select(Alarm.detection_result_id)
            ).all()
        )

        sensors = {
            sensor.id: sensor
            for sensor in session.scalars(select(Sensor)).all()
        }

        created = 0

        for result in results:
            if result.id in existing_ids:
                continue

            sensor = sensors.get(result.sensor_id)
            sensor_type = (
                sensor.sensor_type if sensor else "unknown"
            )

            if result.deviation_pct >= 50:
                severity = "high"
            elif result.deviation_pct >= 25:
                severity = "medium"
            else:
                severity = "low"

            message = (
                f"{sensor_type.capitalize()} reading on "
                f"sensor {result.sensor_id} deviated by "
                f"{result.deviation_pct:.2f}% from its reference. "
                f"Observed={result.observed_value:.4f}, "
                f"reference={result.baseline_value:.4f}."
            )

            session.add(
                Alarm(
                    detection_result_id=result.id,
                    alarm_type="threshold_deviation",
                    severity=severity,
                    message=message,
                    status="open",
                )
            )
            created += 1

        session.commit()

        print(f"New alarms created: {created}")
        print(f"Anomalies reviewed: {len(results)}")


if __name__ == "__main__":
    generate_alarms()
