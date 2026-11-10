import pytest

from tracker.dashboard import budget_status


def page(response):
    return response.get_data(as_text=True)


@pytest.mark.parametrize(
    "spent, budget, expected",
    [
        (0, 10000, "ok"),
        (7999, 10000, "ok"),
        (8000, 10000, "near"),  # exactly 80% counts as near
        (10000, 10000, "near"),  # exactly on budget is not over
        (10001, 10000, "over"),
    ],
)
def test_budget_status(spent, budget, expected):
    assert budget_status(spent, budget) == expected


def test_no_budgets_shows_a_prompt(client, add_transaction, category_ids):
    add_transaction(category_ids["Dining"])
    html = page(client.get("/dashboard?month=2026-10"))
    assert "Budget vs. actual" in html
    assert "No budgets set yet" in html


def test_under_budget(client, add_transaction, set_budgets, category_ids):
    set_budgets(Dining="100")
    add_transaction(category_ids["Dining"], amount="30.00")

    html = page(client.get("/dashboard?month=2026-10"))
    assert "$70.00 left" in html
    assert "$100.00" in html
    assert "30%" in html
    assert "Near limit" not in html
    assert "Over budget" not in html
    assert "No budgets set yet" not in html


def test_near_limit(client, add_transaction, set_budgets, category_ids):
    set_budgets(Dining="100")
    add_transaction(category_ids["Dining"], amount="85.00")

    html = page(client.get("/dashboard?month=2026-10"))
    assert "$15.00 left" in html
    assert "85%" in html
    assert "Near limit" in html
    assert "Over budget" not in html


def test_over_budget(client, add_transaction, set_budgets, category_ids):
    set_budgets(Dining="20")
    add_transaction(category_ids["Dining"], amount="25.00")

    html = page(client.get("/dashboard?month=2026-10"))
    assert "$5.00 over" in html
    assert "125%" in html
    assert "Over budget" in html
    assert "Near limit" not in html


def test_budgeted_category_with_no_spending_is_still_listed(
    client, add_transaction, set_budgets, category_ids
):
    set_budgets(Groceries="300")
    add_transaction(category_ids["Dining"], amount="10.00")

    html = page(client.get("/dashboard?month=2026-10"))
    assert "Groceries" in html
    assert "$300.00 left" in html


def test_spending_in_unbudgeted_categories_is_called_out(
    client, add_transaction, set_budgets, category_ids
):
    set_budgets(Dining="100")
    add_transaction(category_ids["Dining"], amount="30.00")
    add_transaction(category_ids["Rent"], amount="1000.00")

    html = page(client.get("/dashboard?month=2026-10"))
    assert "Another $1,000.00 went to categories without a budget" in html


def test_budgets_apply_to_every_month(client, add_transaction, set_budgets, category_ids):
    set_budgets(Dining="100")
    add_transaction(category_ids["Dining"], date="2026-11-05", amount="5.00")

    html = page(client.get("/dashboard?month=2026-11"))
    assert "$95.00 left" in html


def test_month_with_budgets_but_no_spending(client, set_budgets):
    set_budgets(Groceries="300")

    html = page(client.get("/dashboard?month=2020-06"))
    assert "No spending recorded" in html
    assert "$300.00 left" in html
