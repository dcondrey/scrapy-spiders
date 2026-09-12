from datetime import date

import pytest

from scrapyspiders.extract import find_emails, parse_date_text


def first_email(text):
    found = find_emails(text)
    return found[0] if found else None


@pytest.mark.parametrize(
    "text,expected",
    [
        ("contact me at a@b.com please", "a@b.com"),
        ("first.last@my-studio.com", "first.last@my-studio.com"),
        ("crew@studio123.com", "crew@studio123.com"),
        ("jobs+film@example.com", "jobs+film@example.com"),
        ("hr@mail.example.co.uk", "hr@mail.example.co.uk"),
        ("no email in this string", None),
        ("not-an-email@localhost", None),
    ],
)
def test_email_matching(text, expected):
    assert first_email(text) == expected


def test_finds_all_matches_in_order_without_duplicates():
    assert find_emails("a@b.com then c@d.org then a@b.com") == ["a@b.com", "c@d.org"]


@pytest.mark.parametrize(
    "text,expected",
    [
        ("2026-09-11", date(2026, 9, 11)),
        ("2026-09-11T16:43:56-0700", date(2026, 9, 11)),
        ("09/11/2026", date(2026, 9, 11)),
        ("09.11.2026", date(2026, 9, 11)),
        ("11-Sep-2026", date(2026, 9, 11)),
        ("Sep 11, 2026", date(2026, 9, 11)),
        ("September 11, 2026", date(2026, 9, 11)),
        ("Posted: Sep 9, 2026 by someone", date(2026, 9, 9)),
        ("not a date at all", None),
        ("", None),
        (None, None),
    ],
)
def test_parse_date_text(text, expected):
    assert parse_date_text(text, today=date(2026, 9, 11)) == expected


def test_relative_dates_resolve_against_today():
    today = date(2026, 9, 11)
    assert parse_date_text("3 days ago", today=today) == date(2026, 9, 8)
    assert parse_date_text("2 weeks ago", today=today) == date(2026, 8, 28)


def test_yearless_date_in_the_future_resolves_to_last_year():
    """A Dec 30 listing read on Jan 2 belongs to the previous year."""
    assert parse_date_text("Dec 30", today=date(2026, 1, 2)) == date(2025, 12, 30)


def test_yearless_date_in_the_past_stays_in_this_year():
    assert parse_date_text("Sep 9", today=date(2026, 9, 11)) == date(2026, 9, 9)
