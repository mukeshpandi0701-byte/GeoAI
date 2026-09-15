import os
from pathlib import Path


TEST_DATABASE_PATH = Path(__file__).resolve().parents[1] / "storage" / "test_parcelmap.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DATABASE_PATH.as_posix()}"
