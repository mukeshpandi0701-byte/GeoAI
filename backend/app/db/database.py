import os
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker


DEFAULT_DATABASE_PATH = Path(__file__).resolve().parents[2] / "storage" / "parcelmap.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DATABASE_PATH.as_posix()}")


class Base(DeclarativeBase):
    pass


engine_options = {"connect_args": {"check_same_thread": False}} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, **engine_options)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db():
    """Provide one database session per API request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create the current development tables during application startup."""
    from app.db import models  # noqa: F401 - registers models with Base metadata

    Base.metadata.create_all(bind=engine)
    # Keep local SQLite databases made before processing metadata was added usable.
    if DATABASE_URL.startswith("sqlite"):
        columns = {column["name"] for column in inspect(engine).get_columns("upload_jobs")}
        additions = {
            "processing_started_at": "DATETIME",
            "processing_completed_at": "DATETIME",
            "failed_at": "DATETIME",
            "failure_reason": "TEXT",
            "retry_count": "INTEGER NOT NULL DEFAULT 0",
            "worker_token": "VARCHAR(36)",
            "reviewed_at": "DATETIME",
        }
        with engine.begin() as connection:
            for column_name, column_type in additions.items():
                if column_name not in columns:
                    connection.execute(
                        text(f"ALTER TABLE upload_jobs ADD COLUMN {column_name} {column_type}")
                    )
