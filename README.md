# Austin Picks

Austin Picks is an AI-powered restaurant discovery app for Austin, Texas. It fetches live venue data from Google Places, scores each place using a quality-confidence-value formula, and uses Gemini to explain why each pick is the right choice — returning a focused shortlist instead of an overwhelming ranked list.

## What it does

- **Four automatic Top Picks** — Best Overall, Best Brunch, Best Value, Hidden Gem — refreshed live on every load
- **Ask the Agent search** — type a natural-language request ("quiet coffee shop for working", "cheap tacos with a patio") and get three AI-ranked results with explanations
- **Composite scoring** — 50% rating · 30% review volume (log-scaled) · 20% affordability
- **Gemini blurbs** — each card shows a 2-sentence AI-written summary inferred from review themes

## Architecture

```
Browser (React SPA)
       │
       ├──/──────────────▶  austin-picks-web  (Vite · port 20609 in dev)
       │                         static build in production
       │
       └──/api/──────────▶  api-server  (Node.js / Express · port 8080)
                                │
                                ├── Google Places API (Text Search + Place Details)
                                └── Gemini API via Replit AI proxy
```

- **`artifacts/austin-picks-web/`** — React + Tailwind frontend (Vite)
- **`artifacts/api-server/`** — Node.js Express API server; owns `/api/*` routing in production
- **`api.py`** — FastAPI server (Python); used as a local backend during development (port 5000)
- **`agent.py`** — Gemini helpers (query parsing, blurb generation, ranking)
- **`places_client.py`** — Google Places API (New) client
- **`scoring.py`** — composite 0–1 score per place

## Setup

### 1. Install dependencies

```bash
# Python (FastAPI dev server)
uv sync

# Node.js (frontend + api-server)
pnpm install
```

### 2. Add environment secrets

| Secret | Description |
|---|---|
| `GOOGLE_PLACES_API_KEY` | Google Places API (New) key — must have Places API (New) enabled |
| `AI_INTEGRATIONS_GEMINI_BASE_URL` | Replit-managed Gemini proxy base URL (set automatically by Replit) |
| `AI_INTEGRATIONS_GEMINI_API_KEY` | Replit-managed Gemini proxy key (set automatically by Replit) |

The Google Cloud project behind the Places key must have **Places API (New)** enabled and the key must allow requests to `places.googleapis.com`.

### 3. Start the app

In development, three services run together (Replit manages this automatically):

```bash
# Python FastAPI backend (port 5000)
uvicorn api:app --host 0.0.0.0 --port 5000 --reload

# Node.js API server (port 8080) — handles /api/* in production
pnpm --filter @workspace/api-server run dev

# React frontend with Vite (proxies /api to Node.js api-server)
pnpm --filter @workspace/austin-picks-web run dev
```

## Production deployment

The app publishes as two services on Replit Autoscale:

| Service | Path | What runs |
|---|---|---|
| `austin-picks-web` | `/` | Built React SPA served as static files |
| `api-server` | `/api` | Node.js server — calls Places API and Gemini directly |

Build step: `pnpm --filter @workspace/austin-picks-web run build`

No Python is required in production — the Node.js api-server implements all Places and Gemini logic natively.

## Key design decisions

- **Review text is never stored** — reviews are fetched live and passed to Gemini for theme inference only; they are never written to disk or a database
- **Gemini thinking model** — `gemini-3-flash-preview` uses thinking tokens that count against `maxOutputTokens`; the limit is set to 8192 to avoid truncated JSON responses
- **Routing layering** — Replit's path router sends `/api/*` to the Node.js api-server and `/` to the React SPA; Vite's dev proxy replicates this locally
- **Graceful degradation** — if Gemini is unavailable, cards fall back to Google Places editorial summaries; the app never returns a blank state

## Notes

- All Places queries are biased to Austin, TX (30.2672°N, 97.7431°W, 30 km radius)
- The Hidden Gem pick requires rating ≥ 4.3 and review count < 300 — surfacing quality venues that haven't gone mainstream yet
- Score formula: `0.50 × (rating/5) + 0.30 × log10(reviews+1)/log10(1000) + 0.20 × (4−price_level)/4`
