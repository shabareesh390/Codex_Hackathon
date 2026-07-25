import { useNavigate } from '@tanstack/react-router'
import { FormEvent, useState } from 'react'
import { demoBankCsv, demoLedgerCsv, parseTransactions, readFileAsText, reconcileTransactions } from '../lib/api'

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
    <main className="shell upload-shell">
      <section className="hero card">
        <p className="pill"><i className="ti ti-sparkles" aria-hidden="true" />Agent reconciliation</p>
        <h1>Reconcile UPI settlements with ledger entries in minutes.</h1>
        <p className="lede">Upload messy bank exports and sales ledgers, or load demo data for a polished walkthrough of exact matching, review flags, and agent reasoning.</p>
      </section>

      <form className="card upload-card" onSubmit={submit}>
        <div className="dropzone-grid">
          <label className="dropzone">
            <span className="dropzone-title"><i className="ti ti-building-bank" aria-hidden="true" />Bank / UPI statement</span>
            <span className="dropzone-copy">CSV or PDF export from bank, GPay, PhonePe, or settlement provider.</span>
            <input type="file" accept=".csv,.pdf,text/csv,application/pdf" onChange={(event) => setBankFile(event.target.files?.[0] ?? null)} />
            <span className="file-hint">{bankFile?.name ?? 'Choose statement file'}</span>
          </label>

          <label className="dropzone">
            <span className="dropzone-title"><i className="ti ti-receipt-2" aria-hidden="true" />Sales ledger</span>
            <span className="dropzone-copy">Your shop ledger with dates, amounts, references, and narration.</span>
            <input type="file" accept=".csv,.pdf,text/csv,application/pdf" onChange={(event) => setLedgerFile(event.target.files?.[0] ?? null)} />
            <span className="file-hint">{ledgerFile?.name ?? 'Choose ledger file'}</span>
          </label>
        </div>

        <div className="actions">
          <button className="primary-action" type="submit" disabled={loading}>{loading ? 'Reconciling…' : 'Reconcile uploads'}</button>
          <button type="button" className="ghost-action" onClick={() => void runFlow(true)} disabled={loading}>Load demo data</button>
        </div>
        {error && <p className="error"><i className="ti ti-alert-circle" aria-hidden="true" />{error}</p>}
      </form>
    </main>
  )
}

function requiredFile(file: File | null, label: string): File {
  if (!file) throw new Error(`Please choose a ${label} file first.`)
  return file
}