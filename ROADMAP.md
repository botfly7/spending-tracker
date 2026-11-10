# Roadmap

Each section below is a GitHub Milestone, and each checkbox is a GitHub Issue (use the line as the issue title). Close issues from commit messages or pull requests, e.g. `Fixes #4`.

## Milestone 1: MVP (transaction CRUD)
- [x] Project scaffold (app factory, blueprint, SQLite schema)
- [x] Add a transaction
- [x] List transactions with a running total
- [x] Edit a transaction
- [x] Delete a transaction
- [x] Filter by month and category
- [x] Server-side validation (date, amount, category)
- [x] Tests for routes and input parsing

## Milestone 2: Dashboard
- [ ] Monthly totals by category (SQL `GROUP BY`)
- [ ] Budget table: a monthly target per category
- [ ] Budget vs. actual view with over-budget highlighting
- [ ] Charts with Chart.js (spending by category, spending over time)

## Milestone 3: Accounts
- [ ] Register, log in, and log out
- [ ] Hash passwords with `werkzeug.security`
- [ ] Scope every query to the logged-in user
- [ ] CSRF protection on every POST form
- [ ] Harden the session cookie (secure, httponly, samesite)

## Milestone 4: Extras
- [ ] CSV import from a bank export
- [ ] Auto-categorize by merchant keywords
- [ ] Recurring bills and subscriptions
- [ ] CSV export
- [ ] Manage categories (add, rename, archive)

## Milestone 5: Polish and deploy
- [ ] GitHub Actions workflow that runs `pytest` on every push
- [ ] Database migrations, and optionally PostgreSQL
- [ ] Deploy (Render, Railway, or Fly.io) and put the live link in the README
- [ ] README screenshots or a short GIF
- [ ] Production config (`SECRET_KEY` from the environment, debug off)
