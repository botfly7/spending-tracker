# Spending Tracker

A web app for logging expenses, sorting them into categories, and seeing where the money goes. Built with Flask and SQLite.

**Status:** Milestone 1 (transaction CRUD) is complete and Milestone 2 (dashboard) is complete. See [ROADMAP.md](ROADMAP.md) for what's next.

<!-- Add a screenshot here once the UI settles: ![Spending Tracker screenshot](docs/screenshot.png) -->

## Features

- Add, edit, and delete transactions
- Ten default categories (rent, groceries, dining, transport, and so on)
- Filter the list by month and category, with a running total
- Dashboard with a monthly spending summary by category (SQL `GROUP BY`), month-by-month navigation, and links through to the matching transactions
- Monthly budgets per category, with a budget vs. actual view that flags categories that are near (80%+) or over their limit
- Charts (Chart.js) for spending by category and the last six months, with light and dark themes
- Server-side validation for dates, amounts, and categories
- Money stored as integer cents, so there are no floating-point rounding errors
- Automated tests with pytest

## Run it locally

Requires Python 3.10 or newer.

```bash
git clone https://github.com/<your-username>/spending-tracker.git
cd spending-tracker

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt

flask --app tracker run --debug
```

Then open http://127.0.0.1:5000. The SQLite database is created automatically in `instance/` the first time the app starts.

## Run the tests

```bash
pytest
```

## Project structure

```
spending-tracker/
├── tracker/
│   ├── __init__.py        # app factory (create_app)
│   ├── db.py              # SQLite connection + schema setup
│   ├── schema.sql         # table definitions
│   ├── routes.py          # transaction views + input validation
│   ├── dashboard.py       # monthly summary + budget vs. actual
│   ├── budgets.py         # budget targets form
│   ├── templates/         # Jinja templates
│   └── static/            # style.css, charts.js (Chart.js setup)
├── tests/
├── requirements.txt
├── requirements-dev.txt
└── ROADMAP.md
```

## Design decisions

- **Integer cents.** Amounts are parsed with `Decimal` and stored as whole cents, then formatted back to dollars for display.
- **App factory + blueprint.** `create_app()` lets the tests build an isolated app with its own temporary database.
- **Plain `sqlite3` with parameterized queries.** Small and transparent for now. Moving to SQLAlchemy is an option once the schema grows.

## Known limitations (planned)

- No user accounts yet, so the app is single-user. Milestone 3 adds login and per-user data.
- No CSRF protection yet. It lands with accounts in Milestone 3, so don't deploy publicly before then.
- The charts load Chart.js from the jsDelivr CDN, so they need an internet connection (the tables show the same numbers without it). Before deploying, pin an exact version with a Subresource Integrity hash, or serve the file yourself.
- Set a real `SECRET_KEY` environment variable before deploying. The default is for local development only.
