from datetime import date

import pytest

from tracker.dashboard import month_label, parse_month, shift_month


def page(response):
    return response.get_data(as_text=True)


# ---------- month helpers ----------

@pytest.mark.parametrize(
    "month, delta, expected",
    [
        ("2026-11", 0, "2026-11"),
        ("2026-11", -1, "2026-10"),
        ("2026-11", 1, "2026-12"),
        ("2026-01", -1, "2025-12"),
        ("2026-12", 1, "2027-01"),
        ("2026-03", -15, "2024-12"),
    ],
)
def test_shift_month(month, delta, expected):
    assert shift_month(month, delta) == expected


@pytest.mark.parametrize("raw", ["2026-11", " 2026-11 ", "2000-01", "2100-12"])
def test_parse_month_accepts_valid_months(raw):
    assert parse_month(raw) == raw.strip()


@pytest.mark.parametrize(
    "raw", [None, "", "abc", "2026-1", "2026-00", "2026-13", "1999-12", "2101-01", "0000-01", "9999-12"]
)
def test_parse_month_rejects_invalid_months(raw):
    assert parse_month(raw) is None


def test_month_label():
    assert month_label("2026-11") == "November 2026"
    assert month_label("2026-01") == "January 2026"


# ---------- the dashboard page ----------

def test_dashboard_empty_month(client):
    response = client.get("/dashboard?month=2026-11")
    html = page(response)
    assert response.status_code == 200
    assert "November 2026" in html
    assert "No spending recorded for November 2026" in html


def test_dashboard_totals_by_category(client, add_transaction, category_ids):
    add_transaction(category_ids["Rent"], date="2026-10-01", amount="1000.00")
    add_transaction(category_ids["Dining"], date="2026-10-15", amount="8.00")
    add_transaction(category_ids["Dining"], date="2026-10-20", amount="12.50")
    add_transaction(category_ids["Groceries"], date="2026-11-02", amount="55.00")  # a different month

    html = page(client.get("/dashboard?month=2026-10"))

    assert "$1,020.50" in html  # total for the month
    assert "$1,000.00" in html  # Rent
    assert "$20.50" in html  # Dining (8.00 + 12.50)
    assert '<div class="value">3</div>' in html  # three transactions
    assert '<div class="value">Rent</div>' in html  # top category
    assert "98%" in html and "2%" in html  # shares of the total
    assert "Groceries" not in html  # no spending in this month
    assert "$55.00" not in html


def test_month_boundaries_are_inclusive_of_first_and_last_day(client, add_transaction, category_ids):
    add_transaction(category_ids["Other"], date="2026-09-30", amount="1.00")
    add_transaction(category_ids["Other"], date="2026-10-01", amount="2.00")
    add_transaction(category_ids["Other"], date="2026-10-31", amount="4.00")
    add_transaction(category_ids["Other"], date="2026-11-01", amount="8.00")

    html = page(client.get("/dashboard?month=2026-10"))
    assert '<div class="value">$6.00</div>' in html  # only Oct 1 and Oct 31


def test_categories_are_sorted_by_spending(client, add_transaction, category_ids):
    add_transaction(category_ids["Dining"], amount="5.00")
    add_transaction(category_ids["Rent"], amount="50.00")
    add_transaction(category_ids["Groceries"], amount="20.00")

    html = page(client.get("/dashboard?month=2026-10"))
    assert html.index("Rent") < html.index("Groceries") < html.index("Dining")


def test_category_links_to_filtered_transactions(client, add_transaction, category_ids):
    add_transaction(category_ids["Dining"])

    html = page(client.get("/dashboard?month=2026-10"))
    assert "month=2026-10" in html
    assert f"category={category_ids['Dining']}" in html


# ---------- month navigation ----------

def test_previous_and_next_links(client):
    html = page(client.get("/dashboard?month=2020-06"))
    assert "month=2020-05" in html
    assert "month=2020-07" in html
    assert "Jump to this month" in html


def test_defaults_to_the_current_month(client):
    html = page(client.get("/dashboard"))
    assert month_label(date.today().strftime("%Y-%m")) in html
    assert "Jump to this month" not in html


@pytest.mark.parametrize("bad_month", ["garbage", "2026-13", "0000-01", "1999-12", "9999-12"])
def test_invalid_or_out_of_range_month_falls_back_to_current(client, bad_month):
    response = client.get(f"/dashboard?month={bad_month}")
    assert response.status_code == 200
    assert month_label(date.today().strftime("%Y-%m")) in page(response)


def test_navigation_stops_at_the_supported_range(client):
    first = page(client.get("/dashboard?month=2000-01"))
    assert "Previous month" not in first
    assert "Next month" in first

    last = page(client.get("/dashboard?month=2100-12"))
    assert "Next month" not in last
    assert "Previous month" in last


# ---------- site navigation ----------

def test_nav_links_to_the_dashboard(client):
    html = page(client.get("/"))
    assert 'href="/dashboard"' in html


def test_nav_marks_the_current_page(client):
    html = page(client.get("/dashboard"))
    assert 'aria-current="page"' in html
