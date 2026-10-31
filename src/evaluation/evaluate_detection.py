
import json
from collections import defaultdict
from pathlib import Path

from sqlalchemy import and_, select

from src.database import SessionLocal
from src.models import (
    DetectionResult,
    ScenarioEvent,
    SimulatedTelemetry,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = PROJECT_ROOT / "reports"


def evaluate_detection():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    with SessionLocal() as session:
        rows = session.execute(
            select(
                SimulatedTelemetry,
                ScenarioEvent.scenario_type,
                DetectionResult.result,
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
            .order_by(
                SimulatedTelemetry.event_id,
                SimulatedTelemetry.sensor_id,
                SimulatedTelemetry.timestamp,
            )
        ).all()

    if not rows:
        raise ValueError("No evaluation readings found.")

    counts = defaultdict(int)
    by_scenario = defaultdict(
        lambda: defaultdict(int)
    )
    missing = 0

    for reading, scenario_type, prediction in rows:
        is_control = scenario_type == "normal_control"

        if prediction is None:
            missing += 1
            continue

        predicted_anomaly = prediction == "anomaly"

        if is_control:
            expected_anomaly = False
        else:
            expected_anomaly = True

        if expected_anomaly and predicted_anomaly:
            outcome = "TP"
        elif expected_anomaly and not predicted_anomaly:
            outcome = "FN"
        elif not expected_anomaly and predicted_anomaly:
            outcome = "FP"
        else:
            outcome = "TN"

        counts[outcome] += 1
        by_scenario[scenario_type][outcome] += 1

    tp = counts["TP"]
    fn = counts["FN"]
    fp = counts["FP"]
    tn = counts["TN"]

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    specificity = tn / (tn + fp) if tn + fp else 0.0
    accuracy = (
        (tp + tn) / (tp + tn + fp + fn)
        if tp + tn + fp + fn else 0.0
    )
    
    print("\nRESULTS BY SCENARIO")
    print("-------------------")

    for scenario, values in sorted(by_scenario.items()):
        tp_s = values["TP"]
        fn_s = values["FN"]
        fp_s = values["FP"]
        tn_s = values["TN"]

        total_faults = tp_s + fn_s
        scenario_recall = (
            tp_s / total_faults if total_faults else None
        )

        print(
            f"{scenario}: "
            f"TP={tp_s}, FN={fn_s}, "
            f"FP={fp_s}, TN={tn_s}, "
            f"Recall={scenario_recall:.2%}"
            if scenario_recall is not None
            else (
                f"{scenario}: TP={tp_s}, FN={fn_s}, "
                f"FP={fp_s}, TN={tn_s}, Recall=N/A"
            )
        )

    summary = {
        "evaluation_type": "faults_and_normal_controls",
        "true_positives": tp,
        "false_negatives": fn,
        "false_positives": fp,
        "true_negatives": tn,
        "missing_predictions": missing,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "specificity": round(specificity, 4),
        "accuracy": round(accuracy, 4),
        "by_scenario_type": {
            scenario: dict(values)
            for scenario, values in sorted(by_scenario.items())
        },
        "note": (
            "Control samples are compared with nominal references; "
            "fault samples are compared with their original readings. "
            "Review this difference when interpreting results."
        ),
    }

    output_path = REPORTS_DIR / "evaluation_summary.json"
    output_path.write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )

    print("\nConfusion matrix")
    print("----------------")
    print("                 Predicted anomaly | Predicted normal")
    print(f"Actual anomaly:       {tp:6}      | {fn:6}")
    print(f"Actual normal:        {fp:6}      | {tn:6}")
    print(f"Missing predictions: {missing}")
    print(f"\nPrecision:   {precision:.2%}")
    print(f"Recall:      {recall:.2%}")
    print(f"Specificity: {specificity:.2%}")
    print(f"Accuracy:    {accuracy:.2%}")
    print(f"\nSaved summary to: {output_path}")


if __name__ == "__main__":
    evaluate_detection()
