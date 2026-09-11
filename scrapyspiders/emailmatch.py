import re

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)*\.[A-Za-z]{2,}")


def find_emails(text):
    return EMAIL_RE.findall(text)


def find_first_email(text):
    match = EMAIL_RE.search(text)
    return match.group(0) if match else None
