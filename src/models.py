
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Facility(Base):
    __tablename__ = "facilities"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    location: Mapped[str] = mapped_column(String, nullable=False)


class Equipment(Base):
    """Common information shared by pumps, tanks, and valves."""

    __tablename__ = "equipment"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    facility_id: Mapped[str] = mapped_column(
        ForeignKey("facilities.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    equipment_type: Mapped[str] = mapped_column(String, nullable=False)
    lifecycle_state: Mapped[str] = mapped_column(
        String, default="active", nullable=False
    )


class Pump(Base):
    __tablename__ = "pumps"

    equipment_id: Mapped[str] = mapped_column(
        ForeignKey("equipment.id"), primary_key=True
    )
    rated_flow: Mapped[float] = mapped_column(Float, nullable=False)
    shutoff_head: Mapped[float] = mapped_column(Float, nullable=False)
    curve_coefficient: Mapped[float] = mapped_column(Float, nullable=False)


class Tank(Base):
    __tablename__ = "tanks"

    equipment_id: Mapped[str] = mapped_column(
        ForeignKey("equipment.id"), primary_key=True
    )
    capacity: Mapped[float] = mapped_column(Float, nullable=False)
    initial_level: Mapped[float] = mapped_column(Float, nullable=False)

    __table_args__ = (
        CheckConstraint("capacity > 0", name="ck_tank_capacity_positive"),
        CheckConstraint(
            "initial_level >= 0 AND initial_level <= capacity",
            name="ck_tank_level_within_capacity",
        ),
    )


class Valve(Base):
    __tablename__ = "valves"

    equipment_id: Mapped[str] = mapped_column(
        ForeignKey("equipment.id"), primary_key=True
    )
    valve_type: Mapped[str] = mapped_column(String, nullable=False)
    initial_state: Mapped[str] = mapped_column(String, nullable=False)


class Pipe(Base):
    __tablename__ = "pipes"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    facility_id: Mapped[str] = mapped_column(
        ForeignKey("facilities.id"), nullable=False
    )
    source_equipment_id: Mapped[str] = mapped_column(
        ForeignKey("equipment.id"), nullable=False
    )
    target_equipment_id: Mapped[str] = mapped_column(
        ForeignKey("equipment.id"), nullable=False
    )
    length: Mapped[float] = mapped_column(Float, nullable=False)
    diameter: Mapped[float] = mapped_column(Float, nullable=False)

    __table_args__ = (
        CheckConstraint("length > 0", name="ck_pipe_length_positive"),
        CheckConstraint("diameter > 0", name="ck_pipe_diameter_positive"),
        CheckConstraint(
            "source_equipment_id != target_equipment_id",
            name="ck_pipe_distinct_endpoints",
        ),
    )


class Sensor(Base):
    __tablename__ = "sensors"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    facility_id: Mapped[str] = mapped_column(
        ForeignKey("facilities.id"), nullable=False
    )
    equipment_id: Mapped[str | None] = mapped_column(
        ForeignKey("equipment.id"), nullable=True
    )
    sensor_type: Mapped[str] = mapped_column(String, nullable=False)
    unit: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(
        String, default="active", nullable=False
    )


class Telemetry(Base):
    __tablename__ = "telemetry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sensor_id: Mapped[str] = mapped_column(
        ForeignKey("sensors.id"), nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    quality_status: Mapped[str] = mapped_column(
        String, default="good", nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "sensor_id", "timestamp", name="uq_telemetry_sensor_timestamp"
        ),
    )
    

class ScenarioEvent(Base):
    __tablename__ = "scenario_events"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    facility_id: Mapped[str] = mapped_column(
        ForeignKey("facilities.id"), nullable=False
    )
    equipment_id: Mapped[str | None] = mapped_column(
        ForeignKey("equipment.id"), nullable=True
    )
    scenario_type: Mapped[str] = mapped_column(String, nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    severity: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(
        String, default="planned", nullable=False
    )

