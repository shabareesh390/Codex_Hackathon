from __future__ import annotations

import importlib.util
import json
import os
from dataclasses import dataclass
from decimal import Decimal
from difflib import SequenceMatcher
from typing import Any

from backend.types.transaction import Transaction


@dataclass(frozen=True)
class FuzzyRules:
    amount_tolerance_percent: Decimal = Decimal("1.0")
    date_tolerance_days: int = 2
    minimum_candidate_score: int = 45

    def to_dict(self) -> dict[str, Any]:
        return {"amount_tolerance_percent": str(self.amount_tolerance_percent), "date_tolerance_days": self.date_tolerance_days, "minimum_candidate_score": self.minimum_candidate_score}


def plan_fuzzy_matching(rules: FuzzyRules | None = None) -> dict[str, Any]:
    rules = rules or FuzzyRules()
    return {"step": "plan", "strategy": "Filter candidates by date drift and amount tolerance, then compare narration/reference context and ask OpenAI to choose when configured.", "rules": rules.to_dict()}


def propose_fuzzy_matches(unmatched_bank: list[Transaction], unmatched_ledger: list[Transaction], rules: FuzzyRules | None = None) -> dict[str, Any]:
    rules = rules or FuzzyRules()
    trace = [plan_fuzzy_matching(rules)]
    proposals = []
    used_ledger: set[int] = set()
    for bank_tx in unmatched_bank:
        candidates = [(idx, tx, _candidate_score(bank_tx, tx, rules)) for idx, tx in enumerate(unmatched_ledger) if idx not in used_ledger]
        candidates = [item for item in candidates if item[2] >= rules.minimum_candidate_score]
        candidates.sort(key=lambda item: item[2], reverse=True)
        trace.append({"step": "propose", "bank": bank_tx.to_dict(), "candidate_count": len(candidates), "candidate_scores": [{"ledger": tx.to_dict(), "score": score} for _, tx, score in candidates[:5]]})
        if not candidates:
            continue
        openai_choice, warning = _openai_choose(bank_tx, candidates[:5])
        if warning:
            trace.append({"step": "warning", "message": warning, "fallback": "deterministic_scorer"})
        chosen_index, chosen_tx, score = openai_choice or candidates[0]
        used_ledger.add(chosen_index)
        proposals.append({"bank": bank_tx, "ledger": chosen_tx, "confidence": score, "explanation": _explain(bank_tx, chosen_tx, score)})
        trace.append({"step": "final_decision", "bank": bank_tx.to_dict(), "ledger": chosen_tx.to_dict(), "confidence": score, "explanation": proposals[-1]["explanation"]})
    return {"matches": proposals, "trace": trace, "rules": rules.to_dict()}


def _candidate_score(bank: Transaction, ledger: Transaction, rules: FuzzyRules) -> int:
    date_score = max(0, 35 - 15 * max(abs((bank.date - ledger.date).days) - rules.date_tolerance_days, 0))
    amount_diff = abs(bank.amount - ledger.amount)
    tolerance = max(abs(bank.amount), Decimal("1.00")) * rules.amount_tolerance_percent / Decimal("100")
    amount_score = 35 if amount_diff <= tolerance else max(0, 35 - int((amount_diff / max(abs(bank.amount), Decimal("1.00"))) * 100))
    narration_score = int(30 * SequenceMatcher(None, bank.narration.lower(), ledger.narration.lower()).ratio())
    ref_bonus = 10 if bank.reference_id and bank.reference_id == ledger.reference_id else 0
    return min(100, date_score + amount_score + narration_score + ref_bonus)


def _openai_choose(bank: Transaction, candidates: list[tuple[int, Transaction, int]]) -> tuple[tuple[int, Transaction, int] | None, str | None]:
    if not os.getenv("OPENAI_API_KEY"):
        return None, None
    if importlib.util.find_spec("openai") is None:
        return None, "OpenAI package is unavailable; falling back to deterministic scorer."

    client = _openai_client()
    try:
        response = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            input="Choose the best ledger match as JSON with index, confidence, explanation.\n" + json.dumps({"bank": bank.to_dict(), "candidates": [{"index": idx, "transaction": tx.to_dict(), "score": score} for idx, tx, score in candidates]}),
        )
        data = json.loads(response.output_text)
        for idx, tx, _ in candidates:
            if idx == int(data["index"]):
                return (idx, tx, int(data.get("confidence", _candidate_score(bank, tx, FuzzyRules())))), None
        return None, "OpenAI matcher returned no usable candidate; falling back to deterministic scorer."
    except Exception as exc:
        return None, f"OpenAI matcher failed ({exc.__class__.__name__}: {exc}); falling back to deterministic scorer."


def _openai_client() -> Any:
    from openai import OpenAI

    return OpenAI()


def _explain(bank: Transaction, ledger: Transaction, score: int) -> str:
    date_drift = abs((bank.date - ledger.date).days)
    amount_diff = abs(bank.amount - ledger.amount)
    return f"Likely same payment: amount differs by ₹{amount_diff}, date drift is {date_drift} day(s), and narration context is similar enough for {score}% confidence."
