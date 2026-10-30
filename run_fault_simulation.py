
from src.database import SessionLocal, create_database
from src.simulator.fault_simulator import simulate_faults


def main():
    create_database()

    with SessionLocal() as session:
        try:
            simulate_faults(session)
            session.commit()
            print("Fault simulation completed.")
        except Exception:
            session.rollback()
            raise


if __name__ == "__main__":
    main()
