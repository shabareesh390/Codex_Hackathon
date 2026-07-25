import { Link } from '@tanstack/react-router'
import type { ReactNode } from 'react'
import type { Match, ReconcileResult, Transaction } from '../types'

export function ResultsScreen() {
  const raw = sessionStorage.getItem('reconcileResult')
  const result = raw ? (JSON.parse(raw) as ReconcileResult) : null

  if (!result) {
    return <main className="shell card empty-state"><p className="pill"><i className="ti ti-info-circle" aria-hidden="true" />Agent reconciliation</p><h1>No reconciliation run yet.</h1><Link className="ghost-action inline-action" to="/">Go upload files</Link></main>
  }

  return (
    <main className="shell">
      <header className="results-header card">
        <div>
          <p className="pill"><i className="ti ti-chart-dots-3" aria-hidden="true" />Agent reconciliation</p>
          <h1>Reconciliation summary</h1>
          <p className="lede">{result.metrics.matched_count} exact matches from {result.metrics.bank_total} bank rows before the review agent handled ambiguous rows.</p>
        </div>
        <Link className="ghost-action inline-action" to="/">Run again</Link>
      </header>

      <section className="columns">
        <ResultPanel tone="matched" icon="ti-circle-check" title="Matched" count={result.matched.length}>
          {result.matched.map((match, index) => <MatchCard key={index} match={match} />)}
        </ResultPanel>
        <ResultPanel tone="flagged" icon="ti-alert-triangle" title="Flagged for review" count={result.flagged_for_review.length}>
          {result.flagged_for_review.map((item, index) => (
            <article className="tx-card" key={index}>
              <strong>{item.type}</strong>
              <p>{item.explanation}</p>
              <TransactionLine label="Bank" tx={item.bank} />
              <TransactionLine label="Ledger" tx={item.ledger} />
            </article>
          ))}
        </ResultPanel>
        <ResultPanel tone="unmatched" icon="ti-circle-x" title="Unmatched" count={result.unmatched.bank.length + result.unmatched.ledger.length}>
          {result.unmatched.bank.map((tx, index) => <TransactionLine key={`b-${index}`} label="Bank" tx={tx} />)}
          {result.unmatched.ledger.map((tx, index) => <TransactionLine key={`l-${index}`} label="Ledger" tx={tx} />)}
        </ResultPanel>
      </section>

      <section className="card trace">
        <div className="section-heading">
          <i className="ti ti-terminal-2" aria-hidden="true" />
          <div>
            <h2>Agent trace</h2>
            <p>Plan, proposal, review, and final-decision steps shown for the demo.</p>
          </div>
        </div>
        <pre>{JSON.stringify(result.trace.slice(0, 8), null, 2)}</pre>
      </section>
    </main>
  )
}

function ResultPanel({ tone, icon, title, count, children }: { tone: string; icon: string; title: string; count: number; children: ReactNode }) {
  return <section className={`card panel ${tone}`}><h2><span><i className={`ti ${icon}`} aria-hidden="true" />{title}</span><b>{count}</b></h2><div className="stack">{children}</div></section>
}

function MatchCard({ match }: { match: Match }) {
  return <article className="tx-card"><strong>{match.confidence}% confidence</strong><p>{match.explanation ?? match.review_explanation ?? `Matched by ${match.rule}`}</p><TransactionLine label="Bank" tx={match.bank} /><TransactionLine label="Ledger" tx={match.ledger} /></article>
}

function TransactionLine({ label, tx }: { label: string; tx: Transaction }) {
  return <div className="transaction"><span>{label}</span><b>₹{tx.amount}</b><small>{tx.date} · {tx.reference_id || 'no ref'} · {tx.narration}</small></div>
}
