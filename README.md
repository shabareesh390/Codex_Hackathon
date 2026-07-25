# UPI Recon Agent

Stateless Python parsing and reconciliation functions for Indian MSME UPI/bank statement reconciliation.

## Current stages

1. Normalized transaction schema and CSV/PDF parsing.
2. Rule-based exact matching by reference ID, then amount/date.
3. Agentic fuzzy matching proposal and self-review trace for ambiguous rows.

Run tests with:

```bash
pytest
```
