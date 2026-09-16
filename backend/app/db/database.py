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
    # Keep local SQLite databases made before the review timestamp was added usable.
    if DATABASE_URL.startswith("sqlite"):
        columns = {column["name"] for column in inspect(engine).get_columns("upload_jobs")}
        if "reviewed_at" not in columns:
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE upload_jobs ADD COLUMN reviewed_at DATETIME"))
