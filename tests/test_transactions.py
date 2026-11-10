import pytest

from tracker.db import get_db


def post_transaction(client, category_id, **overrides):
    data = {
        "date": "2026-11-09",
        "amount": "12.50",
        "category_id": str(category_id),
        "description": "Lunch",
        "payment_method": "Debit",
    }
    data.update(overrides)
    return client.post("/add", data=data, follow_redirects=True)


def page(response):
    return response.get_data(as_text=True)


def count_transactions(app):
    with app.app_context():
        return get_db().execute("SELECT COUNT(*) FROM transactions").fetchone()[0]


def test_empty_index(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "No transactions yet" in page(response)
    assert "$0.00" in page(response)


def test_default_categories_are_seeded(category_ids):
    assert len(category_ids) == 10
    assert "Groceries" in category_ids


def test_add_transaction(client, app, category_ids):
    response = post_transaction(client, category_ids["Dining"])
    html = page(response)
    assert response.status_code == 200
    assert "Transaction added." in html
    assert "Lunch" in html
    assert "$12.50" in html
    assert count_transactions(app) == 1


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"amount": "abc"}, "Enter an amount"),
        ({"amount": "-3"}, "Enter an amount"),
        ({"amount": "1.234"}, "Enter an amount"),
        ({"date": "11/09/2026"}, "Enter a valid date"),
        ({"category_id": "9999"}, "Choose a category"),
        ({"category_id": ""}, "Choose a category"),
        ({"description": "x" * 201}, "200 characters or fewer"),
    ],
)
def test_add_rejects_invalid_input(client, app, category_ids, overrides, message):
    response = client.post(
        "/add",
        data={
            "date": "2026-11-09",
            "amount": "12.50",
            "category_id": str(category_ids["Dining"]),
            "description": "Lunch",
            "payment_method": "Debit",
            **overrides,
        },
    )
    assert response.status_code == 400
    assert message in page(response)
    assert count_transactions(app) == 0


def test_invalid_form_keeps_what_the_user_typed(client, category_ids):
    response = client.post(
        "/add",
        data={
            "date": "2026-11-09",
            "amount": "oops",
            "category_id": str(category_ids["Rent"]),
            "description": "Keep me",
            "payment_method": "",
        },
    )
    assert response.status_code == 400
    assert 'value="Keep me"' in page(response)


def test_edit_transaction(client, app, category_ids):
    post_transaction(client, category_ids["Dining"])

    form = client.get("/1/edit")
    assert form.status_code == 200
    assert 'value="12.50"' in page(form)

    response = client.post(
        "/1/edit",
        data={
            "date": "2026-11-10",
            "amount": "20.00",
            "category_id": str(category_ids["Groceries"]),
            "description": "Weekly shop",
            "payment_method": "Cash",
        },
        follow_redirects=True,
    )
    html = page(response)
    assert "Transaction updated." in html
    assert "Weekly shop" in html
    assert "$20.00" in html
    assert "Lunch" not in html
    assert count_transactions(app) == 1


def test_edit_missing_transaction_returns_404(client):
    assert client.get("/999/edit").status_code == 404
    assert client.post("/999/edit", data={}).status_code == 404


def test_delete_transaction(client, app, category_ids):
    post_transaction(client, category_ids["Dining"])
    response = client.post("/1/delete", follow_redirects=True)
    assert "Transaction deleted." in page(response)
    assert count_transactions(app) == 0


def test_delete_requires_post(client, app, category_ids):
    post_transaction(client, category_ids["Dining"])
    assert client.get("/1/delete").status_code == 405
    assert count_transactions(app) == 1


def test_delete_missing_transaction_returns_404(client):
    assert client.post("/999/delete").status_code == 404


def test_filter_by_month_and_category(client, category_ids):
    post_transaction(
        client, category_ids["Dining"], date="2026-11-09", amount="12.50", description="November pizza"
    )
    post_transaction(
        client, category_ids["Rent"], date="2026-10-01", amount="1000.00", description="October landlord"
    )
    post_transaction(
        client, category_ids["Dining"], date="2026-10-15", amount="8.00", description="October tacos"
    )

    everything = page(client.get("/"))
    assert "3 transactions" in everything
    assert "$1,020.50" in everything

    october = page(client.get("/?month=2026-10"))
    assert "October landlord" in october
    assert "October tacos" in october
    assert "November pizza" not in october
    assert "$1,008.00" in october

    dining = page(client.get(f"/?category={category_ids['Dining']}"))
    assert "November pizza" in dining
    assert "October tacos" in dining
    assert "October landlord" not in dining

    both = page(client.get(f"/?month=2026-10&category={category_ids['Dining']}"))
    assert "October tacos" in both
    assert "October landlord" not in both
    assert "November pizza" not in both
    assert "1 transaction" in both
    assert "1 transactions" not in both


def test_filter_with_no_matches(client, category_ids):
    post_transaction(client, category_ids["Dining"])
    html = page(client.get("/?month=2020-01"))
    assert "No transactions match these filters." in html


def test_malformed_filters_are_ignored(client, category_ids):
    post_transaction(client, category_ids["Dining"])
    html = page(client.get("/?month=garbage&category=abc"))
    assert "Lunch" in html


def test_user_text_is_escaped(client, category_ids):
    post_transaction(client, category_ids["Other"], description="<script>alert(1)</script>")
    html = page(client.get("/"))
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html
