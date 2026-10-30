
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from src.models import Base


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

DATABASE_URL = f"sqlite:///{(DATA_DIR / 'industrial_monitoring.db').as_posix()}"

engine = create_engine(DATABASE_URL)


@event.listens_for(engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(bind=engine)


def create_database():
    Base.metadata.create_all(engine)
    print(f"Database created at: {DATA_DIR / 'industrial_monitoring.db'}")


if __name__ == "__main__":
    create_database()
