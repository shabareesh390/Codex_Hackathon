from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from backend.types.transaction import Transaction, transaction_from_dict


@dataclass(frozen=True)
class MatchRules:
    reference_id_enabled: bool = True
    amount_date_enabled: bool = True
    date_tolerance_days: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "reference_id_enabled": self.reference_id_enabled,
            "amount_date_enabled": self.amount_date_enabled,
            "date_tolerance_days": self.date_tolerance_days,
        }


def reconcile_exact(bank: list[Transaction], ledger: list[Transaction], rules: MatchRules | None = None) -> dict[str, Any]:
    rules = rules or MatchRules()
    unmatched_bank = bank[:]
    unmatched_ledger = ledger[:]
    matched: list[dict[str, Any]] = []

    if rules.reference_id_enabled:
        matched.extend(_match_by_reference(unmatched_bank, unmatched_ledger))
        unmatched_bank, unmatched_ledger = _remaining(bank, ledger, matched)

    if rules.amount_date_enabled:
        matched.extend(_match_by_amount_date(unmatched_bank, unmatched_ledger, rules.date_tolerance_days))
        unmatched_bank, unmatched_ledger = _remaining(bank, ledger, matched)

    return {
        "rules": rules.to_dict(),
        "matched": matched,
        "unmatched_bank": unmatched_bank,
        "unmatched_ledger": unmatched_ledger,
        "metrics": {
            "bank_total": len(bank),
            "ledger_total": len(ledger),
            "matched_count": len(matched),
            "exact_match_fraction": round(len(matched) / max(len(bank), 1), 4),
        },
    }


def _match_by_reference(bank: list[Transaction], ledger: list[Transaction]) -> list[dict[str, Any]]:
    matches = []
    used_ledger: set[int] = set()
    for bank_index, bank_tx in enumerate(bank):
        if not bank_tx.reference_id:
            continue
        for ledger_index, ledger_tx in enumerate(ledger):
            if ledger_index in used_ledger:
                continue
            if bank_tx.reference_id == ledger_tx.reference_id and ledger_tx.reference_id:
                matches.append(_match_record(bank_index, ledger_index, bank_tx, ledger_tx, "reference_id"))
                used_ledger.add(ledger_index)
                break
    return matches


def _match_by_amount_date(bank: list[Transaction], ledger: list[Transaction], tolerance_days: int) -> list[dict[str, Any]]:
    matches = []
    used_ledger: set[int] = set()
    tolerance = timedelta(days=tolerance_days)
    for bank_index, bank_tx in enumerate(bank):
        for ledger_index, ledger_tx in enumerate(ledger):
            if ledger_index in used_ledger:
                continue
            if bank_tx.amount == ledger_tx.amount and abs(bank_tx.date - ledger_tx.date) <= tolerance:
                matches.append(_match_record(bank_index, ledger_index, bank_tx, ledger_tx, "amount_date"))
                used_ledger.add(ledger_index)
                break
    return matches


def _match_record(bank_index: int, ledger_index: int, bank_tx: Transaction, ledger_tx: Transaction, rule: str) -> dict[str, Any]:
    return {"bank": bank_tx, "ledger": ledger_tx, "rule": rule, "confidence": 100, "bank_index": bank_index, "ledger_index": ledger_index}


def _remaining(bank: list[Transaction], ledger: list[Transaction], matches: list[dict[str, Any]]) -> tuple[list[Transaction], list[Transaction]]:
    used_bank = {id(match["bank"]) for match in matches}
    used_ledger = {id(match["ledger"]) for match in matches}
    return [tx for tx in bank if id(tx) not in used_bank], [tx for tx in ledger if id(tx) not in used_ledger]


def handler(request: Any) -> dict[str, Any]:
    import json

    body = json.loads(request.body or "{}") if hasattr(request, "body") else request
    bank = [transaction_from_dict(item) for item in body.get("bank", [])]
    ledger = [transaction_from_dict(item) for item in body.get("ledger", [])]
    result = reconcile_exact(bank, ledger)
    serializable = {
        **result,
        "matched": [{**m, "bank": m["bank"].to_dict(), "ledger": m["ledger"].to_dict()} for m in result["matched"]],
        "unmatched_bank": [tx.to_dict() for tx in result["unmatched_bank"]],
        "unmatched_ledger": [tx.to_dict() for tx in result["unmatched_ledger"]],
    }
    return {"statusCode": 200, "body": json.dumps(serializable)}
