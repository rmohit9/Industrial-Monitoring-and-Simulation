
from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import func, select

# Make the project root importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database import SessionLocal
from src.models import (
    Alarm,
    DetectionResult,
    Equipment,
    Facility,
    Sensor,
    Telemetry,
)

st.set_page_config(
    page_title="Industrial Monitoring Dashboard",
    page_icon="🏭",
    layout="wide",
)

st.title("🏭 Industrial Monitoring Dashboard")
st.caption("Equipment health, telemetry, anomaly detection, and alarms")

# Read existing database; do not create or modify tables.
@st.cache_data(ttl=30)
def load_overview():
    with SessionLocal() as session:
        metrics = {
            "Facilities": session.scalar(
                select(func.count()).select_from(Facility)
            ),
            "Equipment": session.scalar(
                select(func.count()).select_from(Equipment)
            ),
            "Sensors": session.scalar(
                select(func.count()).select_from(Sensor)
            ),
            "Telemetry readings": session.scalar(
                select(func.count()).select_from(Telemetry)
            ),
            "Detected anomalies": session.scalar(
                select(func.count())
                .select_from(DetectionResult)
                .where(DetectionResult.result == "anomaly")
            ),
            "Alarms": session.scalar(
                select(func.count()).select_from(Alarm)
            ),
        }

        recent = session.execute(
            select(
                Telemetry.timestamp,
                Telemetry.sensor_id,
                Sensor.sensor_type,
                Sensor.unit,
                Telemetry.value,
            )
            .join(Sensor, Sensor.id == Telemetry.sensor_id)
            .order_by(Telemetry.timestamp.desc())
            .limit(2000)
        ).all()

        sensor_rows = session.execute(
            select(Sensor.id, Sensor.sensor_type, Sensor.unit)
            .order_by(Sensor.id)
        ).all()

    telemetry_df = pd.DataFrame(
        recent,
        columns=["timestamp", "sensor_id", "sensor_type", "unit", "value"],
    )
    sensors_df = pd.DataFrame(
        sensor_rows,
        columns=["sensor_id", "sensor_type", "unit"],
    )

    return metrics, telemetry_df, sensors_df


try:
    metrics, telemetry_df, sensors_df = load_overview()

    metric_cols = st.columns(3)
    for col, (label, value) in zip(metric_cols, list(metrics.items())[:3]):
        col.metric(label, f"{value:,}")

    metric_cols = st.columns(3)
    for col, (label, value) in zip(metric_cols, list(metrics.items())[3:]):
        col.metric(label, f"{value:,}")

    st.divider()
    st.subheader("Telemetry explorer")

    if telemetry_df.empty:
        st.info("No telemetry readings were found in the database.")
    else:
        telemetry_df["timestamp"] = pd.to_datetime(
            telemetry_df["timestamp"]
        )

        selected_type = st.selectbox(
            "Sensor type",
            ["All"] + sorted(
                telemetry_df["sensor_type"].dropna().unique().tolist()
            ),
        )

        filtered = telemetry_df.copy()
        if selected_type != "All":
            filtered = filtered[
                filtered["sensor_type"] == selected_type
            ]

        available_sensors = sorted(
            filtered["sensor_id"].dropna().unique().tolist()
        )
        selected_sensors = st.multiselect(
            "Sensors",
            available_sensors,
            default=available_sensors[:3],
        )

        chart_df = filtered[
            filtered["sensor_id"].isin(selected_sensors)
        ].sort_values("timestamp")

        if chart_df.empty:
            st.info("Select at least one sensor to display its readings.")
        else:
            fig = px.line(
                chart_df,
                x="timestamp",
                y="value",
                color="sensor_id",
                title="Recent telemetry readings",
                hover_data=["sensor_type", "unit"],
            )
            fig.update_layout(
                xaxis_title="Timestamp",
                yaxis_title="Measured value",
                legend_title="Sensor",
            )
            st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Latest alarms")

    with SessionLocal() as session:
        alarm_rows = session.execute(
            select(
                Alarm.created_at,
                Alarm.alarm_type,
                Alarm.severity,
                Alarm.status,
                Alarm.message,
            )
            .order_by(Alarm.created_at.desc())
            .limit(20)
        ).all()

    alarm_df = pd.DataFrame(
        alarm_rows,
        columns=["Created at", "Type", "Severity", "Status", "Message"],
    )

    if alarm_df.empty:
        st.info("No alarms found.")
    else:
        st.dataframe(alarm_df, use_container_width=True, hide_index=True)

    if st.button("Refresh dashboard"):
        st.cache_data.clear()
        st.rerun()

except Exception as exc:
    st.error("Could not load the dashboard data.")
    st.exception(exc)
    st.info(
        "Check that data/industrial_monitoring.db exists and that "
        "the database quality checks pass."
    )
