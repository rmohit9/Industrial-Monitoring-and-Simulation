
from collections import defaultdict

from sqlalchemy import select

from src.database import SessionLocal
from src.models import ScenarioEvent, SimulatedTelemetry


def inspect_fault_deviations():
    stats = defaultdict(
        lambda: {
            "count": 0,
            "changed": 0,
            "unchanged": 0,
            "max_deviation_pct": 0.0,
        }
    )

    with SessionLocal() as session:
        rows = session.execute(
            select(
                ScenarioEvent.scenario_type,
                SimulatedTelemetry.baseline_value,
                SimulatedTelemetry.simulated_value,
            )
            .join(
                ScenarioEvent,
                ScenarioEvent.id == SimulatedTelemetry.event_id,
            )
        ).all()

    for scenario, baseline, observed in rows:
        item = stats[scenario]
        item["count"] += 1

        difference = abs(observed - baseline)

        if difference > 1e-6:
            item["changed"] += 1
        else:
            item["unchanged"] += 1

        if abs(baseline) > 1e-6:
            deviation_pct = difference / abs(baseline) * 100
        else:
            deviation_pct = 100.0 if difference > 1e-6 else 0.0

        item["max_deviation_pct"] = max(
            item["max_deviation_pct"],
            deviation_pct,
        )

    print("\nFAULT DEVIATION REPORT")
    print("----------------------")

    for scenario, item in sorted(stats.items()):
        print(f"\nScenario: {scenario}")
        print(f"Total readings: {item['count']}")
        print(f"Changed readings: {item['changed']}")
        print(f"Unchanged readings: {item['unchanged']}")
        print(
            "Maximum deviation: "
            f"{item['max_deviation_pct']:.2f}%"
        )


if __name__ == "__main__":
    inspect_fault_deviations()
