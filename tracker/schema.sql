CREATE TABLE IF NOT EXISTS categories (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

-- Money is stored as integer cents to avoid floating-point rounding errors.
-- Dates are stored as ISO-8601 text (YYYY-MM-DD), which sorts correctly.
CREATE TABLE IF NOT EXISTS transactions (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    date           TEXT    NOT NULL,
    amount_cents   INTEGER NOT NULL CHECK (amount_cents > 0),
    category_id    INTEGER NOT NULL REFERENCES categories (id),
    description    TEXT    NOT NULL DEFAULT '',
    payment_method TEXT    NOT NULL DEFAULT '',
    created_at     TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions (date);
CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions (category_id);
