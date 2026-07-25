from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from decimal import Decimal
from typing import Any, Literal

TransactionSource = Literal["bank", "ledger"]


@dataclass(frozen=True)
class Transaction:
    date: date
    amount: Decimal
    reference_id: str
    narration: str
    source: TransactionSource

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["date"] = self.date.isoformat()
        data["amount"] = str(self.amount)
        return data


def transaction_from_dict(data: dict[str, Any]) -> Transaction:
    return Transaction(
        date=date.fromisoformat(str(data["date"])),
        amount=Decimal(str(data["amount"])),
        reference_id=str(data.get("reference_id", "")).strip(),
        narration=" ".join(str(data.get("narration", "")).split()),
        source=data["source"],
    )
