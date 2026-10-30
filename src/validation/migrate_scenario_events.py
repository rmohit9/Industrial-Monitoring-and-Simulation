
import sqlite3

from src.database import DATA_DIR


DB_PATH = DATA_DIR / "industrial_monitoring.db"


def main():
    with sqlite3.connect(DB_PATH) as conn:
        columns = {
            row[1]
            for row in conn.execute(
                "PRAGMA table_info(scenario_events)"
            )
        }

        if not columns:
            raise RuntimeError(
                "scenario_events table not found. "
                "Run python -m src.database first."
            )

        if "pipe_id" not in columns:
            conn.execute(
                "ALTER TABLE scenario_events "
                "ADD COLUMN pipe_id VARCHAR REFERENCES pipes(id)"
            )
            print("Added pipe_id column.")

        if "sensor_id" not in columns:
            conn.execute(
                "ALTER TABLE scenario_events "
                "ADD COLUMN sensor_id VARCHAR REFERENCES sensors(id)"
            )
            print("Added sensor_id column.")

        conn.commit()

    print("Scenario-event schema migration completed.")


if __name__ == "__main__":
    main()
