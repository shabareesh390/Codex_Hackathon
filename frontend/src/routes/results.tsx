import { Link } from '@tanstack/react-router'
import type { ReactNode } from 'react'
import type { Match, ReconcileResult, Transaction } from '../types'

export function ResultsScreen() {
  const raw = sessionStorage.getItem('reconcileResult')
  const result = raw ? (JSON.parse(raw) as ReconcileResult) : null

  if (!result) {
    return <main className="shell card"><h1>No reconciliation run yet.</h1><Link to="/">Go upload files</Link></main>
  }

  return (
    <main className="shell">
      <header className="results-header card">
        <div>
          <p className="eyebrow">Results</p>
          <h1>Reconciliation summary</h1>
          <p>{result.metrics.matched_count} exact matches from {result.metrics.bank_total} bank rows before the review agent handled ambiguous rows.</p>
        </div>
        <Link className="button-link" to="/">Run again</Link>
      </header>
      <section className="columns">
        <ResultPanel tone="green" title="Matched" count={result.matched.length}>
          {result.matched.map((match, index) => <MatchCard key={index} match={match} />)}
        </ResultPanel>
        <ResultPanel tone="yellow" title="Flagged for Review" count={result.flagged_for_review.length}>
          {result.flagged_for_review.map((item, index) => (
            <article className="tx-card" key={index}>
              <strong>{item.type}</strong>
              <p>{item.explanation}</p>
              <TransactionLine label="Bank" tx={item.bank} />
              <TransactionLine label="Ledger" tx={item.ledger} />
            </article>
          ))}
        </ResultPanel>
        <ResultPanel tone="red" title="Unmatched" count={result.unmatched.bank.length + result.unmatched.ledger.length}>
          {result.unmatched.bank.map((tx, index) => <TransactionLine key={`b-${index}`} label="Bank" tx={tx} />)}
          {result.unmatched.ledger.map((tx, index) => <TransactionLine key={`l-${index}`} label="Ledger" tx={tx} />)}
        </ResultPanel>
      </section>
      <section className="card trace">
        <h2>Agent trace</h2>
        <pre>{JSON.stringify(result.trace.slice(0, 8), null, 2)}</pre>
      </section>
    </main>
  )
}

function ResultPanel({ tone, title, count, children }: { tone: string; title: string; count: number; children: ReactNode }) {
  return <section className={`card panel ${tone}`}><h2>{title} <span>{count}</span></h2><div className="stack">{children}</div></section>
}

function MatchCard({ match }: { match: Match }) {
  return <article className="tx-card"><strong>{match.confidence}% confidence</strong><p>{match.explanation ?? match.review_explanation ?? `Matched by ${match.rule}`}</p><TransactionLine label="Bank" tx={match.bank} /><TransactionLine label="Ledger" tx={match.ledger} /></article>
}

function TransactionLine({ label, tx }: { label: string; tx: Transaction }) {
  return <div className="transaction"><span>{label}</span><b>₹{tx.amount}</b><small>{tx.date} · {tx.reference_id || 'no ref'} · {tx.narration}</small></div>
}
