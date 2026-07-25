export type Transaction = {
  date: string
  amount: string
  reference_id: string
  narration: string
  source: 'bank' | 'ledger'
}

export type Match = {
  bank: Transaction
  ledger: Transaction
  rule?: string
  confidence: number
  explanation?: string
  review_explanation?: string
}

export type ReconcileResult = {
  matched: Match[]
  flagged_for_review: Array<{ bank: Transaction; ledger: Transaction; type: string; explanation: string }>
  unmatched: { bank: Transaction[]; ledger: Transaction[] }
  trace: Array<Record<string, unknown>>
  metrics: { bank_total: number; ledger_total: number; matched_count: number; exact_match_fraction: number }
}
