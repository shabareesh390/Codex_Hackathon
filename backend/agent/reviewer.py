from __future__ import annotations

from decimal import Decimal
from typing import Any

LOW_CONFIDENCE_THRESHOLD = 70


def review_low_confidence(matches: list[dict[str, Any]], threshold: int = LOW_CONFIDENCE_THRESHOLD) -> dict[str, Any]:
    trace = [{"step": "review_plan", "strategy": "Independently re-check matches below threshold and keep only those with plausible date, amount, or narration evidence.", "threshold": threshold}]
    final_matches = []
    discrepancies = []
    for match in matches:
        if match["confidence"] >= threshold:
            final_matches.append(match)
            continue
        bank = match["bank"]
        ledger = match["ledger"]
        amount_diff = abs(bank.amount - ledger.amount)
        date_drift = abs((bank.date - ledger.date).days)
        if amount_diff <= max(abs(bank.amount) * Decimal("0.02"), Decimal("1.00")) and date_drift <= 3:
            reviewed = {**match, "confidence": min(threshold, match["confidence"] + 10), "review_explanation": "Reviewer confirmed despite low confidence because amount and date are still close."}
            final_matches.append(reviewed)
            trace.append({"step": "review", "decision": "confirmed", "match": _serialize(reviewed)})
        else:
            discrepancy = {"bank": bank, "ledger": ledger, "type": "amount-mismatch", "explanation": "Reviewer rejected this as a genuine discrepancy because amount/date evidence is too weak."}
            discrepancies.append(discrepancy)
            trace.append({"step": "review", "decision": "reclassified", "discrepancy": _serialize(discrepancy)})
    return {"final_matches": final_matches, "discrepancies": discrepancies, "trace": trace}


def _serialize(item: dict[str, Any]) -> dict[str, Any]:
    return {key: value.to_dict() if hasattr(value, "to_dict") else value for key, value in item.items()}
