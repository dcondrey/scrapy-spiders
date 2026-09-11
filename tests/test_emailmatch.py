from scrapyspiders.emailmatch import find_emails, find_first_email


def test_matches_plain_address():
    assert find_first_email("contact me at a@b.com please") == "a@b.com"


def test_matches_hyphenated_domain():
    assert find_first_email("first.last@my-studio.com") == "first.last@my-studio.com"


def test_matches_domain_with_digit():
    assert find_first_email("crew@studio123.com") == "crew@studio123.com"


def test_matches_dotted_local_part():
    assert find_first_email("first.last@example.com") == "first.last@example.com"


def test_matches_plus_addressed_local_part():
    assert find_first_email("jobs+film@example.com") == "jobs+film@example.com"


def test_matches_subdomain():
    assert find_first_email("hr@mail.example.co.uk") == "hr@mail.example.co.uk"


def test_no_match_returns_none():
    assert find_first_email("no email in this string") is None


def test_finds_all_matches_in_order():
    text = "a@b.com then c@d.org"
    assert find_emails(text) == ["a@b.com", "c@d.org"]


def test_rejects_missing_tld():
    assert find_first_email("not-an-email@localhost") is None
