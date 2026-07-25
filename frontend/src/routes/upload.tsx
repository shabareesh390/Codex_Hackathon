import { useNavigate } from '@tanstack/react-router'
import { FormEvent, useState } from 'react'
import { demoBankCsv, demoLedgerCsv, parseTransactions, readFileAsText, reconcileTransactions } from '../lib/api'
import type { ReconcileResult } from '../types'

export function UploadScreen() {
  const navigate = useNavigate()
  const [bankFile, setBankFile] = useState<File | null>(null)
  const [ledgerFile, setLedgerFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function runFlow(useDemo: boolean) {
    setLoading(true)
    setError(null)
    try {
      const bankText = useDemo ? demoBankCsv : await readFileAsText(requiredFile(bankFile, 'bank statement'))
      const ledgerText = useDemo ? demoLedgerCsv : await readFileAsText(requiredFile(ledgerFile, 'sales ledger'))
      const bank = await parseTransactions(bankText, useDemo ? 'bank_statement_sample.csv' : bankFile?.name ?? 'bank.csv', 'bank')
      const ledger = await parseTransactions(ledgerText, useDemo ? 'sales_ledger_sample.csv' : ledgerFile?.name ?? 'ledger.csv', 'ledger')
      const result = await reconcileTransactions(bank, ledger)
      sessionStorage.setItem('reconcileResult', JSON.stringify(result))
      await navigate({ to: '/results' })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  function submit(event: FormEvent) {
    event.preventDefault()
    void runFlow(false)
  }

  return (
    <main className="shell">
      <section className="hero card">
        <p className="eyebrow">Indian MSME UPI Reconciliation</p>
        <h1>Upload bank and ledger exports, then let the agent reconcile them.</h1>
        <p>Exact rules clear the easy rows first; ambiguous settlements are flagged with AI-style reasoning traces for review.</p>
      </section>
      <form className="card upload-grid" onSubmit={submit}>
        <label>
          Bank / UPI statement
          <input type="file" accept=".csv,.pdf,text/csv,application/pdf" onChange={(event) => setBankFile(event.target.files?.[0] ?? null)} />
        </label>
        <label>
          Sales ledger
          <input type="file" accept=".csv,.pdf,text/csv,application/pdf" onChange={(event) => setLedgerFile(event.target.files?.[0] ?? null)} />
        </label>
        <div className="actions">
          <button type="submit" disabled={loading}>{loading ? 'Reconciling…' : 'Reconcile uploads'}</button>
          <button type="button" className="secondary" onClick={() => void runFlow(true)} disabled={loading}>Load demo data</button>
        </div>
        {error && <p className="error">{error}</p>}
      </form>
    </main>
  )
}

function requiredFile(file: File | null, label: string): File {
  if (!file) throw new Error(`Please choose a ${label} file first.`)
  return file
}
