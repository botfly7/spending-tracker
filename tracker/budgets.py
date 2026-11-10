"""Monthly budget targets: one optional amount per category."""

from flask import Blueprint, flash, redirect, render_template, request, url_for

from .db import get_categories, get_db
from .routes import parse_amount, plain_amount

bp = Blueprint("budgets", __name__)


@bp.route("/budgets", methods=("GET", "POST"))
def index():
    db = get_db()
    categories = get_categories()

    if request.method == "POST":
        targets, errors = {}, []
        for category in categories:
            raw = request.form.get(f"budget_{category['id']}", "").strip()
            if not raw:
                targets[category["id"]] = None  # blank means "no budget"
                continue
            cents = parse_amount(raw)
            if cents is None:
                errors.append(
                    f"{category['name']}: enter an amount greater than 0 with at most "
                    "two decimal places, or leave it blank."
                )
                continue
            targets[category["id"]] = cents

        if not errors:
            # One transaction: either every change is saved or none of them are.
            with db:
                for category_id, cents in targets.items():
                    if cents is None:
                        db.execute("DELETE FROM budgets WHERE category_id = ?", (category_id,))
                    else:
                        db.execute(
                            "INSERT INTO budgets (category_id, amount_cents) VALUES (?, ?) "
                            "ON CONFLICT (category_id) DO UPDATE SET amount_cents = excluded.amount_cents",
                            (category_id, cents),
                        )
            flash("Budgets saved.")
            return redirect(url_for("budgets.index"))

        for message in errors:
            flash(message, "error")
        values = {c["id"]: request.form.get(f"budget_{c['id']}", "") for c in categories}
        return render_template("budgets.html", categories=categories, values=values), 400

    saved = db.execute("SELECT category_id, amount_cents FROM budgets").fetchall()
    values = {row["category_id"]: plain_amount(row["amount_cents"]) for row in saved}
    return render_template("budgets.html", categories=categories, values=values)
