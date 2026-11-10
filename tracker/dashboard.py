"""Dashboard views: where the money went in a given month."""

from datetime import date

from flask import Blueprint, render_template, request

from .db import get_db
from .routes import MONTH_PATTERN

bp = Blueprint("dashboard", __name__)

# Keeps month navigation inside a range `date` and the templates handle comfortably.
MIN_YEAR, MAX_YEAR = 2000, 2100

# How many months the spending trend chart covers, ending at the selected month.
MONTHS_SHOWN = 6

# A category is flagged as "near its limit" once it has used this much of its budget.
NEAR_LIMIT_PERCENT = 80


def current_month():
    return date.today().strftime("%Y-%m")


def parse_month(raw):
    """Return the input if it is a valid 'YYYY-MM' month in the supported range, else None."""
    raw = (raw or "").strip()
    if not MONTH_PATTERN.match(raw):
        return None
    return raw if MIN_YEAR <= int(raw[:4]) <= MAX_YEAR else None


def shift_month(month, delta):
    """'2026-12', +1 -> '2027-01'. The result may fall outside the supported range."""
    year, number = int(month[:4]), int(month[5:])
    index = year * 12 + (number - 1) + delta
    return f"{index // 12:04d}-{index % 12 + 1:02d}"


def month_label(month):
    """'2026-11' -> 'November 2026'."""
    return date(int(month[:4]), int(month[5:]), 1).strftime("%B %Y")


def short_month_label(month):
    """'2026-11' -> 'Nov 2026' (used on chart axes)."""
    return date(int(month[:4]), int(month[5:]), 1).strftime("%b %Y")


def trend_months(month, count=MONTHS_SHOWN):
    """The `count` months ending at `month`, oldest first."""
    return [shift_month(month, -offset) for offset in range(count - 1, -1, -1)]


def budget_status(spent_cents, budget_cents):
    """'over' once spending passes the budget, 'near' from 80% of it, otherwise 'ok'."""
    if spent_cents > budget_cents:
        return "over"
    if spent_cents * 100 >= budget_cents * NEAR_LIMIT_PERCENT:
        return "near"
    return "ok"


@bp.route("/dashboard")
def index():
    month = parse_month(request.args.get("month")) or current_month()
    previous_month = shift_month(month, -1)
    next_month = shift_month(month, 1)

    # Dates are stored as ISO text, so a half-open range selects exactly one month
    # and can use the index on transactions.date.
    db = get_db()
    rows = db.execute(
        """
        SELECT c.id,
               c.name,
               SUM(t.amount_cents) AS spent_cents,
               COUNT(*)            AS transaction_count
        FROM transactions t
        JOIN categories c ON c.id = t.category_id
        WHERE t.date >= ? AND t.date < ?
        GROUP BY c.id, c.name
        ORDER BY spent_cents DESC, c.name
        """,
        (f"{month}-01", f"{next_month}-01"),
    ).fetchall()

    total_cents = sum(row["spent_cents"] for row in rows)
    categories = [
        {
            "id": row["id"],
            "name": row["name"],
            "spent_cents": row["spent_cents"],
            "count": row["transaction_count"],
            "share": row["spent_cents"] / total_cents * 100,
        }
        for row in rows
    ]

    # Budget vs. actual: every category that has a budget is listed, even if nothing
    # was spent in it this month. Spending comes from the totals computed above.
    budget_rows = db.execute(
        """
        SELECT c.id, c.name, b.amount_cents AS budget_cents
        FROM budgets b
        JOIN categories c ON c.id = b.category_id
        ORDER BY c.id
        """
    ).fetchall()
    spent_by_category = {c["id"]: c["spent_cents"] for c in categories}
    budgets = []
    for row in budget_rows:
        spent_cents = spent_by_category.get(row["id"], 0)
        budgets.append(
            {
                "id": row["id"],
                "name": row["name"],
                "budget_cents": row["budget_cents"],
                "spent_cents": spent_cents,
                "left_cents": abs(row["budget_cents"] - spent_cents),
                "status": budget_status(spent_cents, row["budget_cents"]),
                "used_percent": spent_cents / row["budget_cents"] * 100,
            }
        )

    budget_summary = None
    if budgets:
        budget_total = sum(b["budget_cents"] for b in budgets)
        budgeted_spent = sum(b["spent_cents"] for b in budgets)
        budget_summary = {
            "total_cents": budget_total,
            "spent_cents": budgeted_spent,
            "left_cents": abs(budget_total - budgeted_spent),
            "is_over": budgeted_spent > budget_total,
            "unbudgeted_cents": total_cents - budgeted_spent,
        }

    # Chart data: the same category totals as the table, plus a trend ending at the
    # selected month. Months with no spending count as zero.
    months = trend_months(month)
    trend_rows = db.execute(
        """
        SELECT substr(date, 1, 7) AS month, SUM(amount_cents) AS spent_cents
        FROM transactions
        WHERE date >= ? AND date < ?
        GROUP BY substr(date, 1, 7)
        """,
        (f"{months[0]}-01", f"{next_month}-01"),
    ).fetchall()
    spent_by_month = {row["month"]: row["spent_cents"] for row in trend_rows}
    month_cents = [spent_by_month.get(m, 0) for m in months]

    chart_data = None
    if any(month_cents):
        chart_data = {
            "categories": {
                "labels": [c["name"] for c in categories],
                "cents": [c["spent_cents"] for c in categories],
            },
            "months": {
                "labels": [short_month_label(m) for m in months],
                "cents": month_cents,
                "selected": len(months) - 1,
            },
        }

    return render_template(
        "dashboard.html",
        month=month,
        label=month_label(month),
        previous_month=previous_month if parse_month(previous_month) else None,
        next_month=next_month if parse_month(next_month) else None,
        is_current=month == current_month(),
        categories=categories,
        total_cents=total_cents,
        transaction_count=sum(c["count"] for c in categories),
        top_category=categories[0] if categories else None,
        budgets=budgets,
        budget_summary=budget_summary,
        chart_data=chart_data,
    )
