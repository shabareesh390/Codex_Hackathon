# UPI Recon Agent

Stateless parsing and reconciliation functions plus a React/Vite frontend for Indian MSME UPI/bank statement reconciliation.

## Project layout

- `api/` — thin Vercel Python serverless entrypoints. Vercel maps `api/parse.py` to `/api/parse` and `api/reconcile.py` to `/api/reconcile`.
- `backend/` — importable Python core logic for parsing, exact reconciliation, fuzzy matching, and self-review.
- `frontend/` — React + Vite + TanStack Router app served as static output.
- `sample_data/` — demo bank and ledger CSVs mirrored in the frontend demo-data button.

## Vercel deployment

`vercel.json` has two build entries:

1. `{ "src": "api/*.py", "use": "@vercel/python" }` tells Vercel to package each root `api/*.py` file as a Python serverless function.
2. `{ "src": "frontend/package.json", "use": "@vercel/static-build", "config": { "distDir": "dist" } }` tells Vercel to run the frontend build and serve `frontend/dist`.

It also has four route rules:

1. `/api/(.*)` routes API requests like `/api/parse` and `/api/reconcile` to the matching Python function file.
2. `/assets/(.*)` routes compiled Vite asset requests from `frontend/dist/assets`.
3. Common static-file extensions route directly from the frontend build output.
4. `/(.*)` falls back to `frontend/index.html` so TanStack Router client routes such as `/results` work on refresh.

`pyproject.toml` pins Python 3.14 with `requires-python = ">=3.14,<3.15"`, and `runtime.txt` records the same intent for hosts that read it. Vercel currently supports Python 3.12, 3.13, and 3.14; 3.14 matches the local runtime used for tests in this repo.

## Local development

Preferred full-stack flow, matching production routing:

```bash
npm i -g vercel
cd frontend && npm install && cd ..
vercel dev
```

Then open the local Vercel URL, click **Load demo data**, and the frontend will call `/api/parse` twice followed by `/api/reconcile`.

Frontend-only iteration is also supported:

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api/*` to `http://localhost:3000`, so run `vercel dev` in another terminal when testing live Python functions.

## Backend tests

```bash
pytest -q -v
```
