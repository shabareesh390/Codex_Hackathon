import type { ReconcileResult, Transaction } from '../types'

export const demoBankCsv = `Txn Date,Description,Credit,UTR
01/07/2026, UPI / RAMESH KIRANA / MILK ,"₹1,200.00",UPI001
02-07-26,PhonePe settlement snacks,800,UPI002
03/07/2026,GPay evening sales,499.50,UPI003
05 Jul 2026,UPI split order customer A,300,UPI004A
05 Jul 2026,UPI split order customer A,200,UPI004B
06/07/2026,Missing in ledger,150,UPI005
`

export const demoLedgerCsv = `Date,Narration,Amount,Reference
2026-07-01,Ramesh Kirana milk sale,1200,UPI001
02/07/2026,Snacks phone pe settlement,800,UPI002
04-07-2026,Google Pay evening sales rounded,500,
05/07/2026,Customer A split payment total,500,
`

export async function parseTransactions(fileText: string, filename: string, source: Transaction['source']): Promise<Transaction[]> {
  const response = await fetch('/api/parse', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ file: fileText, filename, source }),
  })
  const payload = await response.json()
  if (!response.ok || payload.error) {
    throw new Error(payload.error ?? 'Failed to parse transactions')
  }
  return Array.isArray(payload) ? payload : JSON.parse(payload.body)
}

export async function reconcileTransactions(bank: Transaction[], ledger: Transaction[]): Promise<ReconcileResult> {
  const response = await fetch('/api/reconcile', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ bank, ledger }),
  })
  const payload = await response.json()
  if (!response.ok || payload.error) {
    throw new Error(payload.error ?? 'Failed to reconcile transactions')
  }
  return payload
}

export function readFileAsText(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result ?? ''))
    reader.onerror = () => reject(reader.error ?? new Error('Could not read file'))
    reader.readAsText(file, 'utf-8')
  })
}
