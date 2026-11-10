"""Dashboard views: where the money went in a given month."""

from datetime import date

from flask import Blueprint, render_template, request

from .db import get_db
from .routes import MONTH_PATTERN

bp = Blueprint("dashboard", __name__)

# Keeps month navigation inside a range `date` and the templates handle comfortably.
MIN_YEAR, MAX_YEAR = 2000, 2100


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


@bp.route("/dashboard")
def index():
    month = parse_month(request.args.get("month")) or current_month()
    previous_month = shift_month(month, -1)
    next_month = shift_month(month, 1)

    # Dates are stored as ISO text, so a half-open range selects exactly one month
    # and can use the index on transactions.date.
    rows = get_db().execute(
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
    )
