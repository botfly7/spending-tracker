import json
import re

import pytest

from tracker.dashboard import short_month_label, trend_months


def page(response):
    return response.get_data(as_text=True)


def chart_data(html):
    """The JSON the page embeds for charts.js, or None if the page has none."""
    match = re.search(r'<script type="application/json" id="chart-data">(.*?)</script>', html, re.S)
    return json.loads(match.group(1)) if match else None


# ---------- helpers ----------

def test_trend_months_ends_at_the_selected_month():
    assert trend_months("2026-11") == [
        "2026-06", "2026-07", "2026-08", "2026-09", "2026-10", "2026-11",
    ]


def test_trend_months_crosses_the_year_boundary():
    assert trend_months("2026-02") == [
        "2025-09", "2025-10", "2025-11", "2025-12", "2026-01", "2026-02",
    ]


def test_short_month_label():
    assert short_month_label("2026-11") == "Nov 2026"


# ---------- the data the charts receive ----------

def test_no_spending_anywhere_means_no_charts(client):
    html = page(client.get("/dashboard?month=2026-10"))
    assert chart_data(html) is None
    assert "<canvas" not in html
    assert "chart.js" not in html


def test_category_data_matches_the_table_order_and_totals(client, add_transaction, category_ids):
    add_transaction(category_ids["Dining"], date="2026-10-15", amount="8.00")
    add_transaction(category_ids["Dining"], date="2026-10-20", amount="12.50")
    add_transaction(category_ids["Rent"], date="2026-10-01", amount="1000.00")
    add_transaction(category_ids["Groceries"], date="2026-10-22", amount="64.20")

    data = chart_data(page(client.get("/dashboard?month=2026-10")))
    assert data["categories"] == {
        "labels": ["Rent", "Groceries", "Dining"],  # largest first, like the table
        "cents": [100000, 6420, 2050],
    }


def test_trend_data_covers_six_months_with_zeros_for_gaps(client, add_transaction, category_ids):
    add_transaction(category_ids["Other"], date="2026-10-10", amount="40.00")
    add_transaction(category_ids["Other"], date="2026-08-05", amount="10.00")
    add_transaction(category_ids["Other"], date="2026-08-25", amount="5.50")

    data = chart_data(page(client.get("/dashboard?month=2026-10")))
    assert data["months"] == {
        "labels": ["May 2026", "Jun 2026", "Jul 2026", "Aug 2026", "Sep 2026", "Oct 2026"],
        "cents": [0, 0, 0, 1550, 0, 4000],
        "selected": 5,
    }


def test_trend_window_includes_the_oldest_month_and_excludes_older_ones(
    client, add_transaction, category_ids
):
    add_transaction(category_ids["Other"], date="2026-05-01", amount="1.00")  # first month shown
    add_transaction(category_ids["Other"], date="2026-04-30", amount="99.00")  # just outside
    add_transaction(category_ids["Other"], date="2026-11-01", amount="99.00")  # after the selected month

    data = chart_data(page(client.get("/dashboard?month=2026-10")))
    assert data["months"]["cents"] == [100, 0, 0, 0, 0, 0]


def test_trend_still_shows_when_the_selected_month_is_empty(client, add_transaction, category_ids):
    add_transaction(category_ids["Dining"], date="2026-10-15", amount="20.00")

    html = page(client.get("/dashboard?month=2026-11"))
    data = chart_data(html)
    assert data["categories"]["labels"] == []
    assert data["months"]["cents"][-1] == 0
    assert data["months"]["cents"][-2] == 2000
    assert 'id="trend-chart"' in html
    assert 'id="category-chart"' not in html  # nothing to rank this month


# ---------- the page around the charts ----------

def test_chart_page_loads_chart_js_and_our_script(client, add_transaction, category_ids):
    add_transaction(category_ids["Dining"])

    html = page(client.get("/dashboard?month=2026-10"))
    assert "cdn.jsdelivr.net/npm/chart.js@4" in html
    assert "/static/charts.js" in html
    assert 'id="category-chart"' in html
    assert 'id="trend-chart"' in html


def test_chart_cards_start_hidden_and_are_described(client, add_transaction, category_ids):
    add_transaction(category_ids["Dining"])

    html = page(client.get("/dashboard?month=2026-10"))
    assert html.count('<figure class="chart-card" hidden>') == 2
    # Each canvas has a text description; the table below carries the same figures.
    assert html.count('role="img"') == 2
    assert "aria-label=" in html


def test_the_chart_script_is_served(client):
    response = client.get("/static/charts.js")
    assert response.status_code == 200
    assert "chart-data" in response.get_data(as_text=True)
    response.close()


@pytest.mark.parametrize("path", ["/", "/budgets", "/add"])
def test_other_pages_do_not_load_chart_js(client, path):
    assert "chart.js" not in page(client.get(path))
