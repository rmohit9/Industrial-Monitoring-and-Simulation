
from src.database import SessionLocal, create_database
from src.simulator.scenario_generator import generate_scenarios


def main():
    create_database()

    with SessionLocal() as session:
        try:
            generate_scenarios(session, number_of_scenarios=12)
            session.commit()
            print("Scenario generation completed.")
        except Exception:
            session.rollback()
            raise


if __name__ == "__main__":
    main()
