
from src.database import SessionLocal, create_database
from src.detection.rule_engine import detect_anomalies


def main():
    create_database()

    with SessionLocal() as session:
        try:
            detect_anomalies(session)
            session.commit()
            print("Anomaly detection completed.")
        except Exception:
            session.rollback()
            raise


if __name__ == "__main__":
    main()
