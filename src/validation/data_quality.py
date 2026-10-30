
import sqlite3
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "industrial_monitoring.db"


def validate_database(expected_telemetry=100_000):
    if not DB_PATH.exists():
        print(f"ERROR: Database not found: {DB_PATH}")
        return False

    errors = []
    warnings = []

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")

        # 1. Check required tables
        required_tables = {
            "facilities", "equipment", "pumps", "tanks",
            "valves", "pipes", "sensors", "telemetry"
        }

        existing_tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }

        missing = required_tables - existing_tables

        if missing:
            errors.append(f"Missing tables: {sorted(missing)}")
            for error in errors:
                print("FAIL:", error)
            return False

        # 2. Check primary key duplicates
        primary_keys = {
            "facilities": "id",
            "equipment": "id",
            "pumps": "equipment_id",
            "tanks": "equipment_id",
            "valves": "equipment_id",
            "pipes": "id",
            "sensors": "id",
            "telemetry": "id",
        }

        for table, column in primary_keys.items():
            query = f"""
                SELECT COUNT(*) FROM (
                    SELECT {column}
                    FROM {table}
                    GROUP BY {column}
                    HAVING COUNT(*) > 1
                )
            """
            duplicates = conn.execute(query).fetchone()[0]

            if duplicates:
                errors.append(
                    f"{table}: {duplicates} duplicated primary keys"
                )

        # 3. Check foreign key integrity
        fk_violations = conn.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        if fk_violations:
            errors.append(
                f"Foreign key violations found: {len(fk_violations)}"
            )

        # 4. Check duplicate sensor timestamps
        duplicate_readings = conn.execute("""
            SELECT COUNT(*)
            FROM (
                SELECT sensor_id, timestamp
                FROM telemetry
                GROUP BY sensor_id, timestamp
                HAVING COUNT(*) > 1
            )
        """).fetchone()[0]

        if duplicate_readings:
            errors.append(
                f"Duplicate sensor/timestamp combinations: "
                f"{duplicate_readings}"
            )

        # 5. Check sensor and equipment facility consistency
        mismatched_sensors = conn.execute("""
            SELECT COUNT(*)
            FROM sensors s
            JOIN equipment e ON s.equipment_id = e.id
            WHERE s.facility_id != e.facility_id
        """).fetchone()[0]

        if mismatched_sensors:
            errors.append(
                f"Sensors assigned to the wrong facility: "
                f"{mismatched_sensors}"
            )

        # 6. Check that pipe endpoints belong to the pipe's facility
        mismatched_pipes = conn.execute("""
            SELECT COUNT(*)
            FROM pipes p
            JOIN equipment source ON source.id = p.source_equipment_id
            JOIN equipment target ON target.id = p.target_equipment_id
            WHERE source.facility_id != p.facility_id
               OR target.facility_id != p.facility_id
        """).fetchone()[0]

        if mismatched_pipes:
            errors.append(
                f"Pipe endpoints in another facility: {mismatched_pipes}"
            )

        # 7. Check tank levels against capacity
        invalid_tanks = conn.execute("""
            SELECT COUNT(*)
            FROM tanks
            WHERE capacity <= 0
               OR initial_level < 0
               OR initial_level > capacity
        """).fetchone()[0]

        if invalid_tanks:
            errors.append(f"Invalid tank levels or capacities: {invalid_tanks}")

        # 8. Check sensor-specific reading ranges
        invalid_levels = conn.execute("""
            SELECT COUNT(*)
            FROM telemetry t
            JOIN sensors s ON s.id = t.sensor_id
            JOIN tanks k ON k.equipment_id = s.equipment_id
            WHERE s.sensor_type = 'level'
              AND (t.value < 0 OR t.value > k.capacity)
        """).fetchone()[0]

        if invalid_levels:
            errors.append(
                f"Tank-level readings outside capacity: {invalid_levels}"
            )

        invalid_values = conn.execute("""
            SELECT COUNT(*)
            FROM telemetry
            WHERE value < 0
        """).fetchone()[0]

        if invalid_values:
            errors.append(
                f"Negative telemetry readings: {invalid_values}"
            )

        # 9. Check expected record counts
        counts = {}

        for table in sorted(required_tables):
            counts[table] = conn.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]

        expected_counts = {
            "facilities": 3,
            "equipment": 110,
            "pumps": 20,
            "tanks": 30,
            "valves": 60,
            "sensors": 100,
        }

        for table, expected in expected_counts.items():
            actual = counts[table]

            if actual != expected:
                errors.append(
                    f"{table}: expected {expected}, found {actual}"
                )

        actual_telemetry = counts["telemetry"]

        if actual_telemetry != expected_telemetry:
            warnings.append(
                f"Telemetry: expected {expected_telemetry:,}, "
                f"found {actual_telemetry:,}"
            )

        # 10. Print report
        print("\n========== DATA QUALITY REPORT ==========")

        for table, count in counts.items():
            print(f"{table:12} : {count:,} rows")

        for warning in warnings:
            print("WARNING:", warning)

        for error in errors:
            print("FAIL:", error)

        if errors:
            print("\nRESULT: FAILED — fix the errors above.")
            return False

        if warnings:
            print("\nRESULT: STRUCTURAL CHECKS PASSED, "
                  "BUT REVIEW THE WARNINGS.")
            return True

        print("\nRESULT: ALL CHECKS PASSED!")
        return True


if __name__ == "__main__":
    success = validate_database()
    sys.exit(0 if success else 1)
