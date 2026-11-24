
import os
from pathlib import Path

import pytest

# Set this BEFORE importing app.py.
# All automated tests will use this separate database.
project_root = Path(__file__).resolve().parents[1]
test_db_path = project_root / "instance" / "civictrack_pytest.db"
test_db_path.parent.mkdir(parents=True, exist_ok=True)

os.environ["DATABASE_URL"] = f"sqlite:///{test_db_path.as_posix()}"

from app import app, db


@pytest.fixture(autouse=True)
def isolated_test_database():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    with app.app_context():
        db.session.remove()
        db.drop_all()
        db.create_all()

        yield

        db.session.remove()
        db.drop_all()
