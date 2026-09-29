"""Pure validation helpers for contract_form.py - kept separate from the
Tkinter code so they can be tested without a display."""

import re

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_NUMERIC_RE = re.compile(r"^[\d\s.,]+$")


def validate_value(kind: str, label: str, value: str) -> str | None:
    """Return a warning message for this value, or None if it looks fine.

    Warnings are advisory, not blocking - the caller decides whether to
    proceed anyway, since real-world data doesn't always fit a regex.
    """
    value = value.strip()
    if kind == "text":
        if not value:
            return f"{label} är tomt"
        return None
    if kind == "email":
        if not value:
            return f"{label} är tomt"
        if not _EMAIL_RE.match(value):
            return f"{label}: ser inte ut som en e-postadress ({value!r})"
        return None
    if kind == "numeric":
        if not value:
            return f"{label} är tomt"
        if not _NUMERIC_RE.match(value):
            return f"{label}: bör bara innehålla siffror ({value!r})"
        return None
    if kind == "date":
        if not value:
            return f"{label} är tomt"
        if not _DATE_RE.match(value):
            return f"{label}: bör vara i formatet ÅÅÅÅ-MM-DD ({value!r})"
        return None
    raise ValueError(f"Unknown kind {kind!r}")


def validate_radio(label: str, selected: str | None) -> str | None:
    if not selected:
        return f"{label}: inget alternativ valt"
    return None
