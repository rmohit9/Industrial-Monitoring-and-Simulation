
from src.database import SessionLocal, create_database
from src.models import Facility, Equipment, Pump, Tank, Valve,Sensor

from src.models import Pipe

from src.generators.telemetry_generator import generate_telemetry

def generate_facilities(session):
    facilities = [
        ("FAC-001", "North Water Treatment Plant", "North Zone"),
        ("FAC-002", "South Water Treatment Plant", "South Zone"),
        ("FAC-003", "Central Water Distribution Plant", "Central Zone"),
    ]

    for facility_id, name, location in facilities:
        if session.get(Facility, facility_id) is None:
            session.add(
                Facility(
                    id=facility_id,
                    name=name,
                    location=location,
                )
            )

    session.flush()
    print("Facilities verified: 3")


def generate_equipment(session):
    # Each equipment record is assigned to an existing facility.
    facility_ids = ["FAC-001", "FAC-002", "FAC-003"]

    for facility_id in facility_ids:
        if session.get(Facility, facility_id) is None:
            raise ValueError(
                f"Required facility does not exist: {facility_id}"
            )

    # Generate 20 pumps
    for i in range(1, 21):
        equipment_id = f"PUMP-{i:03d}"
        facility_id = facility_ids[(i - 1) % 3]

        if session.get(Equipment, equipment_id) is None:
            session.add(
                Equipment(
                    id=equipment_id,
                    facility_id=facility_id,
                    name=f"Pump {i:03d}",
                    equipment_type="pump",
                    lifecycle_state="active",
                )
            )
        session.flush()

        if session.get(Pump, equipment_id) is None:
            session.add(
                Pump(
                    equipment_id=equipment_id,
                    rated_flow=80 + (i % 5) * 10,
                    shutoff_head=45 + (i % 4) * 5,
                    curve_coefficient=0.001,
                )
            )

    # Generate 30 tanks
    for i in range(1, 31):
        equipment_id = f"TANK-{i:03d}"
        facility_id = facility_ids[(i - 1) % 3]

        capacity = 500 + (i % 6) * 100
        initial_level = capacity * (0.4 + (i % 5) * 0.1)

        if session.get(Equipment, equipment_id) is None:
            session.add(
                Equipment(
                    id=equipment_id,
                    facility_id=facility_id,
                    name=f"Tank {i:03d}",
                    equipment_type="tank",
                    lifecycle_state="active",
                )
            )
        session.flush()

        if session.get(Tank, equipment_id) is None:
            session.add(
                Tank(
                    equipment_id=equipment_id,
                    capacity=capacity,
                    initial_level=initial_level,
                )
            )

    # Generate 60 valves
    valve_types = ["gate", "ball", "butterfly"]

    for i in range(1, 61):
        equipment_id = f"VALVE-{i:03d}"
        facility_id = facility_ids[(i - 1) % 3]

        if session.get(Equipment, equipment_id) is None:
            session.add(
                Equipment(
                    id=equipment_id,
                    facility_id=facility_id,
                    name=f"Valve {i:03d}",
                    equipment_type="valve",
                    lifecycle_state="active",
                )
            )
        session.flush()

        if session.get(Valve, equipment_id) is None:
            session.add(
                Valve(
                    equipment_id=equipment_id,
                    valve_type=valve_types[(i - 1) % 3],
                    initial_state="closed" if i % 5 == 0 else "open",
                )
            )

    print("Equipment verified: 20 pumps, 30 tanks, 60 valves")

def generate_pipes(session):

    pipe_count = 1

    # Create a simple topology for each facility
    facilities = ["FAC-001", "FAC-002", "FAC-003"]

    for facility_id in facilities:

        # Each facility gets:
        # Tank -> Pump -> Valve -> Tank connections

        tanks = [
            f"TANK-{i:03d}"
            for i in range(1, 31)
            if (i - 1) % 3 == int(facility_id[-1]) - 1
        ]

        pumps = [
            f"PUMP-{i:03d}"
            for i in range(1, 21)
            if (i - 1) % 3 == int(facility_id[-1]) - 1
        ]

        valves = [
            f"VALVE-{i:03d}"
            for i in range(1, 61)
            if (i - 1) % 3 == int(facility_id[-1]) - 1
        ]


        # Connect available equipment
        for i in range(min(len(pumps), len(tanks), len(valves))):

            connections = [
                (tanks[i], pumps[i]),
                (pumps[i], valves[i]),
                (valves[i], tanks[(i+1) % len(tanks)])
            ]


            for source, target in connections:

                pipe_id = f"PIPE-{pipe_count:03d}"

                if session.get(Pipe, pipe_id) is None:

                    session.add(
                        Pipe(
                            id=pipe_id,
                            facility_id=facility_id,
                            source_equipment_id=source,
                            target_equipment_id=target,
                            length=100 + pipe_count * 2,
                            diameter=200
                        )
                    )

                pipe_count += 1


    print(f"Pipes generated: {pipe_count-1}")
    

def generate_sensors(session):
    sensors_to_create = []

    # 20 flow sensors attached to pumps
    for i in range(1, 21):
        sensors_to_create.append(
            (f"PUMP-{i:03d}", "flow", "L/s")
        )

    # 20 pressure sensors attached to pumps
    for i in range(1, 21):
        sensors_to_create.append(
            (f"PUMP-{i:03d}", "pressure", "kPa")
        )

    # 30 tank-level sensors attached to tanks
    for i in range(1, 31):
        sensors_to_create.append(
            (f"TANK-{i:03d}", "level", "L")
        )

    # 30 pressure sensors attached to valves
    for i in range(1, 31):
        sensors_to_create.append(
            (f"VALVE-{i:03d}", "pressure", "kPa")
        )

    created_count = 0

    for index, (equipment_id, sensor_type, unit) in enumerate(
        sensors_to_create, start=1
    ):
        sensor_id = f"SNS-{index:03d}"

        # Skip sensors already generated on an earlier run
        if session.get(Sensor, sensor_id) is not None:
            continue

        equipment = session.get(Equipment, equipment_id)

        if equipment is None:
            raise ValueError(
                f"Equipment {equipment_id} does not exist. "
                "Generate equipment before sensors."
            )

        session.add(
            Sensor(
                id=sensor_id,
                facility_id=equipment.facility_id,
                equipment_id=equipment_id,
                sensor_type=sensor_type,
                unit=unit,
                status="active",
            )
        )

        created_count += 1

    session.flush()
    print(
        f"Sensors created in this run: {created_count}; "
        f"expected total: 100"
    )

def main():
    create_database()

    with SessionLocal() as session:
        try:
            generate_facilities(session)
            generate_equipment(session)
            generate_pipes(session)
            generate_sensors(session)
            session.commit()
            print("Synthetic master data generated successfully!")
        except Exception:
            session.rollback()
            raise


if __name__ == "__main__":
    main()

    with SessionLocal() as session:
        generate_telemetry(session, readings_per_sensor=1000)
