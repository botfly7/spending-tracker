"""SQLite connection handling and schema setup."""

import sqlite3
from pathlib import Path

from flask import current_app, g

DEFAULT_CATEGORIES = [
    "Rent",
    "Groceries",
    "Dining",
    "Transport",
    "Utilities",
    "Subscriptions",
    "Health",
    "Entertainment",
    "Shopping",
    "Other",
]


def get_db():
    """Return this request's database connection, opening it on first use."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def get_categories():
    return get_db().execute("SELECT id, name FROM categories ORDER BY id").fetchall()


def init_db():
    """Create the tables if they don't exist and seed the default categories once."""
    db = get_db()
    db.executescript(Path(__file__).with_name("schema.sql").read_text())
    if db.execute("SELECT COUNT(*) FROM categories").fetchone()[0] == 0:
        db.executemany(
            "INSERT INTO categories (name) VALUES (?)",
            [(name,) for name in DEFAULT_CATEGORIES],
        )
        db.commit()


def init_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        init_db()
