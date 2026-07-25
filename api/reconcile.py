from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler
from typing import Any

from backend.agent.matcher import propose_fuzzy_matches
from backend.agent.reviewer import review_low_confidence
from backend.api.reconcile import reconcile_exact
from backend.types.transaction import transaction_from_dict


class handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        try:
            payload = self._read_json()
            self._send_json(200, reconcile_payload(payload))
        except Exception as exc:
            self._send_json(400, {"error": str(exc)})

    def do_OPTIONS(self) -> None:
        self._send_json(204, {})

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("content-length", "0"))
        body = self.rfile.read(length).decode("utf-8") if length else "{}"
        return json.loads(body or "{}")

    def _send_json(self, status: int, payload: object) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        if status != 204:
            self.wfile.write(json.dumps(payload).encode("utf-8"))


def reconcile_payload(body: dict[str, Any]) -> dict[str, Any]:
    bank = [transaction_from_dict(item) for item in body.get("bank", [])]
    ledger = [transaction_from_dict(item) for item in body.get("ledger", [])]
    exact = reconcile_exact(bank, ledger)
    fuzzy = propose_fuzzy_matches(exact["unmatched_bank"], exact["unmatched_ledger"])
    reviewed = review_low_confidence(fuzzy["matches"])
    matched = [
        {**match, "bank": match["bank"].to_dict(), "ledger": match["ledger"].to_dict()}
        for match in exact["matched"] + reviewed["final_matches"]
    ]
    flagged = [
        {"bank": item["bank"].to_dict(), "ledger": item["ledger"].to_dict(), "type": item["type"], "explanation": item["explanation"]}
        for item in reviewed["discrepancies"]
    ]
    matched_bank_ids = {id(match["bank"]) for match in reviewed["final_matches"]}
    matched_ledger_ids = {id(match["ledger"]) for match in reviewed["final_matches"]}
    return {
        "matched": matched,
        "flagged_for_review": flagged,
        "unmatched": {
            "bank": [tx.to_dict() for tx in exact["unmatched_bank"] if id(tx) not in matched_bank_ids],
            "ledger": [tx.to_dict() for tx in exact["unmatched_ledger"] if id(tx) not in matched_ledger_ids],
        },
        "trace": fuzzy["trace"] + reviewed["trace"],
        "metrics": exact["metrics"],
    }
