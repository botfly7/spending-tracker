import datetime

import pytest

from tracker.routes import money, parse_amount, parse_date, plain_amount


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("12.50", 1250),
        ("$1,200", 120000),
        ("0.01", 1),
        ("5", 500),
        ("  7.5 ", 750),
        ("10000000", 1_000_000_000),
    ],
)
def test_parse_amount_accepts_valid_input(raw, expected):
    assert parse_amount(raw) == expected


@pytest.mark.parametrize(
    "raw",
    ["", "   ", "abc", "0", "-5", "1.005", "NaN", "Infinity", "1e9", "10000000.01", None],
)
def test_parse_amount_rejects_invalid_input(raw):
    assert parse_amount(raw) is None


def test_parse_date_accepts_iso_dates():
    assert parse_date("2026-11-09") == datetime.date(2026, 11, 9)


@pytest.mark.parametrize("raw", ["", "11/09/2026", "2026-13-01", "2026-02-30", "not a date", None])
def test_parse_date_rejects_invalid_input(raw):
    assert parse_date(raw) is None


def test_money_formatting():
    assert money(0) == "$0.00"
    assert money(5) == "$0.05"
    assert money(1250) == "$12.50"
    assert money(123456789) == "$1,234,567.89"


def test_plain_amount_formatting():
    assert plain_amount(1250) == "12.50"
    assert plain_amount(5) == "0.05"
