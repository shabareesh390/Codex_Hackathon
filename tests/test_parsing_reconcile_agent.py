from decimal import Decimal

from backend.agent.matcher import propose_fuzzy_matches
from backend.agent.reviewer import review_low_confidence
from backend.api.parse import parse_csv, parse_pdf
from backend.api.reconcile import reconcile_exact


def test_csv_parses_messy_dates_currency_and_skips_missing_amount():
    text = """Date,Narration,Amount,Reference
01/07/2026,  UPI sale  ,"₹1,200.50",abc 123
02-07-26,Bad row,,missing
2026-07-03,Another sale,Rs. 99,xyz
"""
    txs = parse_csv(text, "bank")
    assert len(txs) == 2
    assert txs[0].date.isoformat() == "2026-07-01"
    assert txs[0].amount == Decimal("1200.50")
    assert txs[0].reference_id == "ABC123"
    assert txs[0].narration == "UPI sale"


def test_pdf_style_text_blob_parses_transactions():
    blob = "Statement\n01/07/2026 UPI RAMESH KIRANA ₹1,200.00 UPI001\n02-07-26 PhonePe Snacks INR 800 UPI002\n"
    txs = parse_pdf(blob, "bank")
    assert [tx.amount for tx in txs] == [Decimal("1200.00"), Decimal("800.00")]
    assert txs[1].date.isoformat() == "2026-07-02"


def test_exact_reconcile_reports_demo_fraction():
    bank = parse_csv(open("sample_data/bank_statement_sample.csv").read(), "bank")
    ledger = parse_csv(open("sample_data/sales_ledger_sample.csv").read(), "ledger")
    result = reconcile_exact(bank, ledger)
    assert result["metrics"]["matched_count"] == 2
    assert result["metrics"]["exact_match_fraction"] == 0.3333
    assert len(result["unmatched_bank"]) == 4
    assert len(result["unmatched_ledger"]) == 2


def test_fuzzy_matcher_and_reviewer_emit_trace_for_ambiguous_rows():
    bank = parse_csv(open("sample_data/bank_statement_sample.csv").read(), "bank")
    ledger = parse_csv(open("sample_data/sales_ledger_sample.csv").read(), "ledger")
    exact = reconcile_exact(bank, ledger)
    fuzzy = propose_fuzzy_matches(exact["unmatched_bank"], exact["unmatched_ledger"])
    reviewed = review_low_confidence(fuzzy["matches"])
    assert fuzzy["trace"][0]["step"] == "plan"
    assert any(step["step"] == "propose" for step in fuzzy["trace"])
    assert reviewed["trace"][0]["step"] == "review_plan"
    assert fuzzy["matches"]
