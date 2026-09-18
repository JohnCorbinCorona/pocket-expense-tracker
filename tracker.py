"""Expense calculations and CSV tools, kept separate from the web interface."""

import csv
from datetime import date
from decimal import Decimal
import io
import re
from uuid import uuid4

COLUMNS = ["date", "category", "amount", "description"]
MAX_CENTS = 99_999_999_999  # A generous per-entry limit, with exact cents.


def parse_money(text):
    """Accept 1250, 1,250.00, or $1,250.00; return integer cents."""
    cleaned = str(text).strip()
    if cleaned.startswith("$"):
        cleaned = cleaned[1:].strip()
    pattern = r"(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)(?:\.[0-9]{1,2})?"
    if not re.fullmatch(pattern, cleaned):
        raise ValueError("Use a positive amount with up to two decimal places, such as $1,250.00.")
    if len(cleaned) > 20:
        raise ValueError("That amount is too large.")
    cents = int(Decimal(cleaned.replace(",", "")) * 100)
    if not 0 < cents <= MAX_CENTS:
        raise ValueError("Enter an amount between $0.01 and $999,999,999.99.")
    return cents


def money(cents):
    return f"${Decimal(cents) / 100:,.2f}"


def make_expense(day, category, amount, description):
    """Validate one expense and give it a stable ID for deletion."""
    day = str(day).strip()
    try:
        parsed = date.fromisoformat(day)
    except ValueError:
        raise ValueError("Enter a real date using YYYY-MM-DD.") from None
    if parsed.isoformat() != day:
        raise ValueError("Use YYYY-MM-DD for dates.")
    category = str(category or "").strip().title()
    description = str(description or "").strip()
    if not category or not description:
        raise ValueError("Category and description cannot be blank.")
    if len(category) > 60 or len(description) > 300:
        raise ValueError("Keep categories under 61 characters and descriptions under 301.")
    return {"id": uuid4().hex, "date": day, "category": category,
            "cents": parse_money(amount), "description": description}


def monthly_expenses(expenses, month):
    return [item for item in expenses if item["date"].startswith(month)]


def category_totals(expenses):
    totals = {}
    for item in expenses:
        category = item["category"].strip().title()
        totals[category] = totals.get(category, 0) + item["cents"]
    return dict(sorted(totals.items(), key=lambda pair: (-pair[1], pair[0])))


def expense_signature(item):
    return tuple(item[key] for key in ("date", "category", "cents", "description"))


def merge_expenses(existing, incoming, skip_duplicates=True):
    """Return a new list; don't mutate a visitor's data while previewing an import."""
    result = list(existing)
    seen = {expense_signature(item) for item in existing}
    skipped = 0
    for item in incoming:
        signature = expense_signature(item)
        if skip_duplicates and signature in seen:
            skipped += 1
            continue
        result.append(item)
        seen.add(signature)
    return result, skipped


def read_csv(raw):
    """Read the same four-column CSV as the terminal project; report bad rows."""
    if len(raw) > 2 * 1024 * 1024:
        raise ValueError("Choose a CSV file smaller than 2 MB.")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeError:
        raise ValueError("Save the file as a UTF-8 CSV and try again.") from None
    reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
    expenses, errors = [], []
    try:
        if reader.fieldnames is None or set(reader.fieldnames) != set(COLUMNS) or len(reader.fieldnames) != 4:
            raise ValueError("The CSV header must contain date,category,amount,description exactly once each.")
        for row in reader:
            try:
                if None in row:
                    raise ValueError("Unexpected extra columns.")
                if any(not (row.get(field) or "").strip() for field in COLUMNS):
                    raise ValueError("A required field is blank.")
                expenses.append(make_expense(row["date"], row["category"], row["amount"], row["description"]))
            except ValueError as error:
                errors.append(f"Row ending at line {reader.line_num}: {error}")
            if len(expenses) + len(errors) > 10_000:
                raise ValueError("Import at most 10,000 rows at a time.")
    except csv.Error:
        raise ValueError("The CSV has broken quoting or an oversized field. No rows were imported.") from None
    return expenses, errors


def write_csv(expenses):
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=COLUMNS)
    writer.writeheader()
    for item in expenses:
        writer.writerow({"date": item["date"], "category": item["category"],
                         "amount": f"{Decimal(item['cents']) / 100:.2f}",
                         "description": item["description"]})
    return buffer.getvalue().encode("utf-8")
