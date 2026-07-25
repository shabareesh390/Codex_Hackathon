from __future__ import annotations

import csv
import io
import json
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable


from backend.types.transaction import Transaction, TransactionSource

DATE_FORMATS = ("%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y", "%Y-%m-%d", "%d %b %Y", "%d %B %Y")
DATE_COLUMNS = ("date", "txn date", "transaction date", "value date", "payment date")
AMOUNT_COLUMNS = ("amount", "credit", "debit", "paid", "total", "settlement amount")
REFERENCE_COLUMNS = ("reference_id", "reference", "ref", "utr", "upi ref", "transaction id", "txn id")
NARRATION_COLUMNS = ("narration", "description", "details", "remarks", "particulars")
PDF_LINE_RE = re.compile(
    r"(?P<date>\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{1,2}-\d{1,2})\s+"
    r"(?P<narration>.*?)\s+"
    r"(?P<amount>(?:INR|Rs\.?|₹)?\s*-?[\d,]+(?:\.\d{1,2})?)\s*"
    r"(?P<reference>(?:UPI|UTR|REF|TXN)[A-Z0-9/-]*)?$",
    re.IGNORECASE,
)


def parse_file(file: str | Path | bytes, source: TransactionSource, filename: str | None = None) -> list[Transaction]:
    content, name = _read_file(file, filename)
    if _is_pdf(content, name):
        return parse_pdf(content, source)
    return parse_csv(content.decode("utf-8-sig"), source)


def parse_csv(text: str, source: TransactionSource) -> list[Transaction]:
    reader = csv.DictReader(io.StringIO(text))
    transactions: list[Transaction] = []
    for row_number, row in enumerate(reader, start=2):
        transactions.append(_transaction_from_row(row, source, row_number))
    return transactions


def parse_pdf(content: bytes | str, source: TransactionSource) -> list[Transaction]:
    text = content if isinstance(content, str) else _extract_pdf_text(content)
    rows = _rows_from_pdf_text(text)
    return [_transaction_from_row(row, source, row_number) for row_number, row in enumerate(rows, start=1)]


def _extract_pdf_text(content: bytes) -> str:
    import pdfplumber

    with pdfplumber.open(io.BytesIO(content)) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def _rows_from_pdf_text(text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in text.splitlines():
        line = " ".join(line.split())
        if not line:
            continue
        match = PDF_LINE_RE.search(line)
        if match:
            rows.append(match.groupdict(default=""))
            continue
        parsed = next(csv.reader([line])) if "," in line else []
        if len(parsed) >= 3:
            rows.append({"date": parsed[0], "narration": parsed[1], "amount": parsed[2], "reference": parsed[3] if len(parsed) > 3 else ""})
    return rows


def _transaction_from_row(row: dict[str, Any], source: TransactionSource, row_number: int) -> Transaction:
    normalized = {_normalize_key(key): str(value).strip() for key, value in row.items()}
    raw_date = _first_value(normalized, DATE_COLUMNS)
    raw_amount = _first_value(normalized, AMOUNT_COLUMNS)
    parsed_date = parse_date(raw_date)
    parsed_amount = parse_amount(raw_amount)
    if parsed_date is None:
        raise ValueError(f"Could not parse date on row {row_number}: raw value {raw_date!r}; row={normalized!r}")
    if parsed_amount is None:
        raise ValueError(f"Could not parse amount on row {row_number}: raw value {raw_amount!r}; row={normalized!r}")
    return Transaction(
        date=parsed_date,
        amount=parsed_amount,
        reference_id=_clean_reference(_first_value(normalized, REFERENCE_COLUMNS)),
        narration=" ".join(_first_value(normalized, NARRATION_COLUMNS).split()),
        source=source,
    )


def parse_date(value: str) -> date | None:
    value = value.strip()
    for fmt in DATE_FORMATS:
        try:
            from datetime import datetime
            return datetime.strptime(value, fmt).date()
        except (ValueError, TypeError):
            pass
    return None


def parse_amount(value: str) -> Decimal | None:
    cleaned = re.sub(r"(?:INR|Rs\.?|₹|,|\s)", "", value, flags=re.IGNORECASE)
    if cleaned in {"", "-"}:
        return None
    try:
        return Decimal(cleaned).quantize(Decimal("0.01"))
    except InvalidOperation:
        return None


def _read_file(file: str | Path | bytes, filename: str | None) -> tuple[bytes, str]:
    if isinstance(file, bytes):
        return file, filename or "upload"
    path = Path(file)
    if path.suffix.lower() == ".pdf":
        return path.read_bytes(), filename or path.name
    return path.read_text(encoding="utf-8").encode("utf-8"), filename or path.name


def _is_pdf(content: bytes, filename: str) -> bool:
    return filename.lower().endswith(".pdf") or content.startswith(b"%PDF")


def _normalize_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", key.lower()).strip()


def _first_value(row: dict[str, str], candidates: Iterable[str]) -> str:
    for candidate in candidates:
        if candidate in row and row[candidate].strip():
            return row[candidate].strip()
    return ""


def _clean_reference(value: str) -> str:
    return re.sub(r"\s+", "", value).upper()


def handler(request: Any) -> dict[str, Any]:
    body = json.loads(request.body or "{}") if hasattr(request, "body") else request
    transactions = parse_file(body["file"].encode("utf-8"), body.get("source", "bank"), body.get("filename"))
    return {"statusCode": 200, "body": json.dumps([tx.to_dict() for tx in transactions])}
