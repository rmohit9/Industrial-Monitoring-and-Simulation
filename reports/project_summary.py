
import json
from collections import Counter
from pathlib import Path

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import func, select

from src.database import SessionLocal
from src.models import (
    Facility,
    Equipment,
    Pump,
    Tank,
    Valve,
    Pipe,
    Sensor,
    Telemetry,
    ScenarioEvent,
    SimulatedTelemetry,
    DetectionResult,
    Alarm,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORT_PATH = PROJECT_ROOT / "reports" / "project_summary.json"


def project_summary():
    with SessionLocal() as session:
        summary = {
            "project": "Industrial Monitoring and Fault Detection",
            "database_summary": {
                "facilities": session.scalar(
                    select(func.count()).select_from(Facility)
                ),
                "equipment": session.scalar(
                    select(func.count()).select_from(Equipment)
                ),
                "pumps": session.scalar(
                    select(func.count()).select_from(Pump)
                ),
                "tanks": session.scalar(
                    select(func.count()).select_from(Tank)
                ),
                "valves": session.scalar(
                    select(func.count()).select_from(Valve)
                ),
                "pipes": session.scalar(
                    select(func.count()).select_from(Pipe)
                ),
                "sensors": session.scalar(
                    select(func.count()).select_from(Sensor)
                ),
                "telemetry_points": session.scalar(
                    select(func.count()).select_from(Telemetry)
                ),
            },
            "simulation_summary": {
                "scenario_events": session.scalar(
                    select(func.count()).select_from(ScenarioEvent)
                ),
                "simulated_readings": session.scalar(
                    select(func.count()).select_from(SimulatedTelemetry)
                ),
                "detection_results": session.scalar(
                    select(func.count()).select_from(DetectionResult)
                ),
            },
        }

        # Count alarms by severity
        alarm_rows = session.execute(
            select(Alarm.severity, func.count(Alarm.id))
            .group_by(Alarm.severity)
        ).all()

        summary["alarms_by_severity"] = {
            severity: count for severity, count in alarm_rows
        }

        # Count detection results by outcome
        result_rows = session.execute(
            select(DetectionResult.result, func.count(DetectionResult.id))
            .group_by(DetectionResult.result)
        ).all()

        summary["detection_results_by_outcome"] = {
            result: count for result, count in result_rows
        }

        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(
            json.dumps(summary, indent=4),
            encoding="utf-8",
        )

        print(json.dumps(summary, indent=4))
        print(f"\nReport saved to: {REPORT_PATH}")


if __name__ == "__main__":
    project_summary()
