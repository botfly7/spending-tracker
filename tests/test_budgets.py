import sqlite3

import pytest

from tracker import create_app
from tracker.db import get_db


def page(response):
    return response.get_data(as_text=True)


def saved_budgets(app):
    """The budgets table as {category_id: amount_cents}."""
    with app.app_context():
        rows = get_db().execute("SELECT category_id, amount_cents FROM budgets").fetchall()
    return {row["category_id"]: row["amount_cents"] for row in rows}


def test_budgets_page_lists_every_category(client, category_ids):
    response = client.get("/budgets")
    html = page(response)
    assert response.status_code == 200
    assert "Monthly budgets" in html
    for name in category_ids:
        assert name in html
    assert html.count('name="budget_') == len(category_ids)


def test_save_budgets(client, app, category_ids, budget_form):
    response = client.post(
        "/budgets",
        data=budget_form(Rent="1,200.00", Groceries="300"),
        follow_redirects=True,
    )
    html = page(response)
    assert "Budgets saved." in html
    assert 'value="1200.00"' in html  # the form shows what was saved
    assert 'value="300.00"' in html
    assert saved_budgets(app) == {
        category_ids["Rent"]: 120000,
        category_ids["Groceries"]: 30000,
    }


def test_updating_a_budget_replaces_it(app, category_ids, set_budgets):
    set_budgets(Dining="100")
    set_budgets(Dining="150.50")
    assert saved_budgets(app) == {category_ids["Dining"]: 15050}


def test_blank_field_removes_a_budget(app, category_ids, set_budgets):
    set_budgets(Dining="100", Rent="500")
    set_budgets(Rent="500")  # Dining left blank
    assert saved_budgets(app) == {category_ids["Rent"]: 50000}


@pytest.mark.parametrize("bad_amount", ["abc", "0", "-5", "1.234", "1e12"])
def test_invalid_amount_saves_nothing(client, app, budget_form, bad_amount):
    response = client.post("/budgets", data=budget_form(Rent="500", Groceries=bad_amount))
    html = page(response)
    assert response.status_code == 400
    assert "Groceries: enter an amount" in html
    assert f'value="{bad_amount}"' in html  # keeps what was typed
    assert 'value="500"' in html
    assert saved_budgets(app) == {}  # Rent was valid, but nothing is saved


def test_unknown_form_fields_are_ignored(client, app, category_ids, budget_form):
    data = budget_form(Rent="500")
    data["budget_9999"] = "100"  # not a real category
    response = client.post("/budgets", data=data)
    assert response.status_code == 302
    assert saved_budgets(app) == {category_ids["Rent"]: 50000}


def test_existing_database_gets_the_budgets_table(tmp_path):
    database = str(tmp_path / "old.sqlite")
    create_app({"TESTING": True, "DATABASE": database})

    # Simulate a database created before budgets existed.
    connection = sqlite3.connect(database)
    connection.execute("DROP TABLE budgets")
    connection.commit()
    connection.close()

    app = create_app({"TESTING": True, "DATABASE": database})
    with app.app_context():
        get_db().execute("SELECT * FROM budgets").fetchall()  # raises if the table is missing


def test_nav_links_to_budgets_and_marks_the_current_page(client):
    assert 'href="/budgets"' in page(client.get("/"))
    assert 'aria-current="page"' in page(client.get("/budgets"))
