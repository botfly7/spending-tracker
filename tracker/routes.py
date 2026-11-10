"""Views for adding, listing, editing, and deleting transactions."""

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from .db import get_categories, get_db

bp = Blueprint("transactions", __name__)

MAX_AMOUNT = Decimal("10000000")  # a sanity limit, not a business rule
MAX_TEXT_LENGTH = 200
MONTH_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


# ---------- template filters ----------

@bp.app_template_filter("money")
def money(cents):
    """12345 -> '$123.45' (used for display)."""
    return f"${cents // 100:,}.{cents % 100:02d}"


@bp.app_template_filter("plain_amount")
def plain_amount(cents):
    """12345 -> '123.45' (used to pre-fill the edit form)."""
    return f"{cents // 100}.{cents % 100:02d}"


# ---------- input parsing and validation ----------

def parse_amount(raw):
    """Turn input like '12.50' or '$1,200' into integer cents, or None if invalid."""
    cleaned = (raw or "").strip().replace("$", "").replace(",", "")
    try:
        amount = Decimal(cleaned)
    except InvalidOperation:
        return None
    if not amount.is_finite() or amount <= 0 or amount > MAX_AMOUNT:
        return None
    if amount != amount.quantize(Decimal("0.01")):
        return None  # more than two decimal places
    return int(amount * 100)


def parse_date(raw):
    """Parse strict YYYY-MM-DD input into a date, or None if invalid."""
    try:
        return datetime.strptime((raw or "").strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def validate_transaction_form(form):
    """Return (cleaned_values, errors) for the add/edit form."""
    errors = []

    tx_date = parse_date(form.get("date"))
    if tx_date is None:
        errors.append("Enter a valid date (YYYY-MM-DD).")

    amount_cents = parse_amount(form.get("amount"))
    if amount_cents is None:
        errors.append("Enter an amount greater than 0 with at most two decimal places.")

    category_id = form.get("category_id", type=int)
    exists = (
        category_id is not None
        and get_db().execute("SELECT 1 FROM categories WHERE id = ?", (category_id,)).fetchone()
    )
    if not exists:
        errors.append("Choose a category.")

    description = (form.get("description") or "").strip()
    payment_method = (form.get("payment_method") or "").strip()
    if len(description) > MAX_TEXT_LENGTH or len(payment_method) > MAX_TEXT_LENGTH:
        errors.append(f"Description and payment method must be {MAX_TEXT_LENGTH} characters or fewer.")

    cleaned = {
        "date": tx_date.isoformat() if tx_date else None,
        "amount_cents": amount_cents,
        "category_id": category_id,
        "description": description,
        "payment_method": payment_method,
    }
    return cleaned, errors


def get_transaction_or_404(transaction_id):
    row = get_db().execute(
        "SELECT id, date, amount_cents, category_id, description, payment_method "
        "FROM transactions WHERE id = ?",
        (transaction_id,),
    ).fetchone()
    if row is None:
        abort(404)
    return row


# ---------- views ----------

@bp.route("/")
def index():
    month = request.args.get("month", "").strip()
    if not MONTH_PATTERN.match(month):
        month = ""
    category_id = request.args.get("category", type=int)

    # Only fixed SQL fragments are joined here; every value goes through a ? placeholder.
    clauses, params = [], []
    if month:
        clauses.append("substr(t.date, 1, 7) = ?")
        params.append(month)
    if category_id is not None:
        clauses.append("t.category_id = ?")
        params.append(category_id)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    transactions = get_db().execute(
        f"""
        SELECT t.id, t.date, t.amount_cents, t.description, t.payment_method,
               c.name AS category
        FROM transactions t
        JOIN categories c ON c.id = t.category_id
        {where}
        ORDER BY t.date DESC, t.id DESC
        """,
        params,
    ).fetchall()

    return render_template(
        "index.html",
        transactions=transactions,
        total_cents=sum(row["amount_cents"] for row in transactions),
        categories=get_categories(),
        month=month,
        category_id=category_id,
    )


@bp.route("/add", methods=("GET", "POST"))
def add():
    if request.method == "POST":
        cleaned, errors = validate_transaction_form(request.form)
        if not errors:
            db = get_db()
            db.execute(
                "INSERT INTO transactions (date, amount_cents, category_id, description, payment_method) "
                "VALUES (:date, :amount_cents, :category_id, :description, :payment_method)",
                cleaned,
            )
            db.commit()
            flash("Transaction added.")
            return redirect(url_for("transactions.index"))
        for message in errors:
            flash(message, "error")
        return render_template(
            "form.html", heading="Add transaction", values=request.form, categories=get_categories()
        ), 400

    return render_template(
        "form.html",
        heading="Add transaction",
        values={"date": date.today().isoformat()},
        categories=get_categories(),
    )


@bp.route("/<int:transaction_id>/edit", methods=("GET", "POST"))
def edit(transaction_id):
    row = get_transaction_or_404(transaction_id)

    if request.method == "POST":
        cleaned, errors = validate_transaction_form(request.form)
        if not errors:
            db = get_db()
            db.execute(
                "UPDATE transactions SET date = :date, amount_cents = :amount_cents, "
                "category_id = :category_id, description = :description, "
                "payment_method = :payment_method WHERE id = :id",
                {**cleaned, "id": transaction_id},
            )
            db.commit()
            flash("Transaction updated.")
            return redirect(url_for("transactions.index"))
        for message in errors:
            flash(message, "error")
        return render_template(
            "form.html", heading="Edit transaction", values=request.form, categories=get_categories()
        ), 400

    values = {
        "date": row["date"],
        "amount": plain_amount(row["amount_cents"]),
        "category_id": row["category_id"],
        "description": row["description"],
        "payment_method": row["payment_method"],
    }
    return render_template(
        "form.html", heading="Edit transaction", values=values, categories=get_categories()
    )


@bp.route("/<int:transaction_id>/delete", methods=("POST",))
def delete(transaction_id):
    get_transaction_or_404(transaction_id)
    db = get_db()
    db.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
    db.commit()
    flash("Transaction deleted.")
    return redirect(url_for("transactions.index"))
