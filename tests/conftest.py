import pytest

from tracker import create_app
from tracker.db import get_db


@pytest.fixture
def app(tmp_path):
    """A fresh app with its own temporary database for every test."""
    return create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test",
            "DATABASE": str(tmp_path / "test.sqlite"),
        }
    )


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def category_ids(app):
    """Map of category name -> id, read from the seeded database."""
    with app.app_context():
        rows = get_db().execute("SELECT id, name FROM categories").fetchall()
    return {row["name"]: row["id"] for row in rows}
