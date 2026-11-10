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


@pytest.fixture
def add_transaction(client):
    """A helper that creates a transaction through the real form."""

    def _add(category_id, **overrides):
        data = {
            "date": "2026-10-15",
            "amount": "10.00",
            "category_id": str(category_id),
            "description": "Test purchase",
            "payment_method": "Debit",
        }
        data.update(overrides)
        response = client.post("/add", data=data)
        assert response.status_code == 302  # a redirect means it was saved
        return response

    return _add


@pytest.fixture
def budget_form(category_ids):
    """Build the budgets form data: budget_form(Rent="1200", Dining="80")."""

    def _build(**amounts):
        data = {f"budget_{category_id}": "" for category_id in category_ids.values()}
        for name, amount in amounts.items():
            data[f"budget_{category_ids[name]}"] = amount
        return data

    return _build


@pytest.fixture
def set_budgets(client, budget_form):
    """A helper that saves budgets through the real form: set_budgets(Dining="100")."""

    def _set(**amounts):
        response = client.post("/budgets", data=budget_form(**amounts))
        assert response.status_code == 302  # a redirect means they were saved

    return _set
