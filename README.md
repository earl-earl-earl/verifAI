# verifAI

An AI-powered fact-checking platform. Submit a claim or paste an article — the system scrapes trusted news and fact-check sources, runs it through Gemini AI, and returns a verdict with a confidence score and cited evidence.

---

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
- [Data Flow](#data-flow)
- [Deployment](#deployment)
- [CI/CD](#cicd)
- [Observability](#observability)
- [Development Notes](#development-notes)
- [Roadmap](#roadmap)

---

## Overview

verifAI is a full-stack portfolio project demonstrating end-to-end system design across backend, AI, mobile, web, infrastructure, and observability. Every technology in the stack is load-bearing — nothing is included for show.

**What it does:**
1. User submits a claim via the web or mobile app
2. API queues a scraping job to Upstash Redis
3. A worker scrapes trusted sources (eg. Reuters, AP News, Snopes, PolitiFact) using httpx + BeautifulSoup
4. Gemini AI analyzes the claim against the scraped evidence
5. A verdict (`true` / `false` / `misleading` / `unverifiable`) is returned with a confidence score and explanation
6. Results are streamed back to the client in real time via SSE or WebSocket

---

## Tech Stack

### Backend
| Technology | Purpose |
|---|---|
| **FastAPI** | REST API, SSE streaming, WebSocket endpoints |
| **Pydantic v2** | Request/response validation and document models |
| **Motor** | Async MongoDB driver |
| **httpx** | Async HTTP client for fetching source pages |
| **BeautifulSoup4** | HTML parsing and content extraction |

### AI
| Technology | Purpose |
|---|---|
| **Gemini API** | Verdict generation, confidence scoring, explanation |

### Data
| Technology | Purpose |
|---|---|
| **MongoDB Atlas** | Managed cloud database — claims, reports, sources, users (free M0 tier) |
| **Upstash Redis** | Serverless Redis — job queue + result cache (free tier, REST-based) |

### Web
| Technology | Purpose |
|---|---|
| **Next.js** | Web application — dashboard, claim feed, report detail |
| **Zod** | Frontend schema validation, mirrors Pydantic models 1:1 |

### Mobile
| Technology | Purpose |
|---|---|
| **Expo** | Cross-platform mobile app with share-sheet claim submission |

### Containerization
| Technology | Purpose |
|---|---|
| **Docker** | CI-only image builds — no local Docker install required |
| **docker-compose** | Local dev environment — API + worker only |

### Cloud (GCP)
| Technology | Purpose |
|---|---|
| **Cloud Run** | Hosts FastAPI container, scales to zero (free when idle) |
| **Cloud Run Jobs** | On-demand scraper execution |
| **Pub/Sub** | Job trigger queue between API and scraper |
| **Container Registry** | Stores Docker images built by CI |

### CI/CD & Monorepo
| Technology | Purpose |
|---|---|
| **Turborepo** | Monorepo task pipelines, smart build caching, affected-only builds |
| **GitHub Actions** | Build, lint, test, push Docker images, deploy to Cloud Run |

### Observability
| Technology | Purpose |
|---|---|
| **OpenTelemetry** | Distributed tracing across FastAPI and worker process |
| **Sentry** | Error tracking for API, web app, and mobile app |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENTS                              │
│         Next.js (web)          Expo (mobile)                │
└──────────────────┬──────────────────┬───────────────────────┘
                   │  HTTP / WS / SSE  │
┌──────────────────▼──────────────────▼───────────────────────┐
│                    GCP CLOUD RUN                            │
│                     FastAPI API                             │
│         POST /claims   GET /claims/:id/stream               │
└──────┬───────────────────────┬──────────────────────────────┘
       │                       │
       ▼                       ▼
┌─────────────┐      ┌─────────────────────┐
│   Upstash   │      │    MongoDB Atlas    │
│    Redis    │      │  (M0 free cluster)  │
│  job queue  │      └─────────────────────┘
│  + cache    │
└──────┬──────┘
       │
       ▼
┌───────────────────────────────────────────┐
│         GCP CLOUD RUN JOB                 │
│         Scraper Worker                    │
│  1. httpx fetches 4 sources concurrently  │
│  2. BeautifulSoup extracts content        │
│  3. Call Gemini API for verdict           │
│  4. Write result to MongoDB Atlas + cache │
└───────────────────────────────────────────┘
```

### Request lifecycle

```
Client
  │
  ├─ POST /api/v1/claims          → API creates report (status: pending)
  │                               → pushes job to Upstash Redis queue
  │                               ← returns { id, status: "pending" }
  │
  ├─ GET /api/v1/claims/:id/stream  (SSE)
  │     ↕ polls cache every 2s
  │     ← event: status_update { status: "scraping" }
  │     ← event: status_update { status: "analyzing" }
  │     ← event: result         { verdict, confidence, sources, explanation }
  │
Worker (separate process)
  ├─ brpop Upstash Redis queue
  ├─ httpx fetches 4 sources concurrently
  ├─ BeautifulSoup extracts relevant content
  ├─ Gemini API returns structured verdict
  └─ Writes final report to MongoDB Atlas + updates Redis cache
```

---

## Project Structure

```
verifai/
├── apps/
│   ├── api/                        # FastAPI backend
│   │   ├── app/
│   │   │   ├── core/
│   │   │   │   ├── config.py       # pydantic-settings, all env vars
│   │   │   │   ├── redis.py        # Upstash Redis client singleton
│   │   │   │   └── database.py     # Motor MongoDB Atlas client singleton
│   │   │   ├── models/
│   │   │   │   └── claim.py        # Pydantic v2 models (ClaimReport, Source, etc.)
│   │   │   ├── routers/
│   │   │   │   ├── claims.py       # POST /claims, GET /claims/:id, SSE stream
│   │   │   │   └── health.py       # GET /health, GET /health/ready
│   │   │   ├── services/
│   │   │   │   ├── cache.py        # Redis read/write for reports
│   │   │   │   ├── queue.py        # Redis job push/pop
│   │   │   │   ├── scraper.py      # httpx + BeautifulSoup scraping service
│   │   │   │   └── gemini.py       # Gemini AI verdict service
│   │   │   ├── workers/
│   │   │   │   └── scrape_worker.py # Standalone worker process
│   │   │   └── main.py             # FastAPI app entrypoint
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├── web/                        # Next.js web app
│   │   ├── app/                    # App router
│   │   ├── components/
│   │   └── package.json
│   │
│   └── mobile/                     # Expo mobile app
│       ├── app/                    # Expo Router
│       └── package.json
│
├── packages/
│   ├── shared-types/               # Zod schemas shared between web and mobile
│   │   └── src/index.ts            # Mirrors Pydantic models 1:1
│   └── ui/                         # Shared React/React Native components
│
├── .github/
│   └── workflows/
│       ├── ci.yml                  # Lint + test on every PR
│       └── deploy.yml              # Build Docker image + deploy to Cloud Run on main
│
├── docker-compose.yml              # Local dev: API + worker (no DB or Redis needed)
├── turbo.json                      # Turborepo pipeline config
├── package.json                    # Root workspace config
└── .gitignore
```

---

## Getting Started

### Prerequisites

- Node.js 20+
- Python 3.11+
- A MongoDB Atlas account (free at [cloud.mongodb.com](https://cloud.mongodb.com))
- An Upstash account (free at [upstash.com](https://upstash.com))
- A Gemini API key (free at [aistudio.google.com](https://aistudio.google.com))

### 1. Clone and install

```bash
git clone https://github.com/yourusername/verifai.git
cd verifai
npm install
```

### 2. Set up Python environment

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure MongoDB Atlas

1. Create a free M0 cluster at [cloud.mongodb.com](https://cloud.mongodb.com)
2. Create a database user and whitelist your IP (or use `0.0.0.0/0` for dev)
3. Copy your connection string into `.env`

### 4. Configure Upstash Redis

1. Create a free Redis database at [upstash.com](https://upstash.com)
2. Copy the REST URL and token into `.env`

### 5. Configure environment variables

```bash
cp .env.example .env
# Fill in GEMINI_API_KEY, MONGODB_URL, REDIS_REST_URL, REDIS_REST_TOKEN
```

### 6. Run the API

```bash
cd apps/api
uvicorn app.main:app --reload --port 8000
```

### 7. Run the worker (separate terminal)

```bash
cd apps/api
python -m app.workers.scrape_worker
```

### 8. Run the web app

```bash
cd apps/web
npm run dev
```

### 9. Run the mobile app

```bash
cd apps/mobile
npx expo start
```

API docs available at `http://localhost:8000/docs`

---

## Environment Variables

```env
# App
DEBUG=false

# MongoDB Atlas
MONGODB_URL=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB_NAME=verifai

# Upstash Redis
REDIS_URL=rediss://<your-upstash-url>:6379
REDIS_REST_URL=https://<your-upstash-url>.upstash.io
REDIS_REST_TOKEN=your_token_here
REDIS_CACHE_TTL=3600

# Gemini
GEMINI_API_KEY=your_key_here

# Sentry (optional for local dev)
SENTRY_DSN_API=
SENTRY_DSN_WEB=
SENTRY_DSN_MOBILE=
```

---

## API Reference

### `POST /api/v1/claims`

Submit a claim for fact-checking. Returns immediately with a report ID.

**Request**
```json
{ "claim": "The Great Wall of China is visible from space." }
```

**Response** `202 Accepted`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Claim submitted. Use /claims/{id}/stream to follow progress."
}
```

---

### `GET /api/v1/claims/:id`

Get the current state of a report.

**Response** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "claim": "The Great Wall of China is visible from space.",
  "status": "done",
  "verdict": "false",
  "confidence": 0.97,
  "explanation": "Multiple sources including NASA and AP News confirm the wall is too narrow to be visible from low Earth orbit with the naked eye.",
  "sources": [
    {
      "url": "https://apnews.com/...",
      "title": "NASA Debunks Great Wall Myth",
      "snippet": "Astronauts aboard the ISS have confirmed...",
      "scraped_at": "2025-05-14T10:00:00Z"
    }
  ],
  "created_at": "2025-05-14T10:00:00Z",
  "updated_at": "2025-05-14T10:00:05Z"
}
```

---

### `GET /api/v1/claims/:id/stream`

Server-Sent Events stream. Emits status updates until the report reaches a terminal state.

**Events**
```
event: status_update
data: { "status": "scraping", ... }

event: status_update
data: { "status": "analyzing", ... }

event: result
data: { "status": "done", "verdict": "false", "confidence": 0.97, ... }
```

---

### `GET /health/ready`

Readiness check — verifies Upstash Redis and MongoDB Atlas connectivity and returns queue length.

---

## Data Flow

```
1. POST /claims
   └─ Create ClaimReport (status: pending)
   └─ repository.insert()               → MongoDB Atlas (permanent)
   └─ cache_service.set_report()        → Upstash Redis (TTL: 1hr)
   └─ queue_service.push_scrape_job()   → Upstash Redis list (LPUSH)
   └─ Return { id, status: pending }

2. Worker loop (brpop)
   └─ pop job from Upstash Redis
   └─ update status → "scraping"        → Upstash Redis cache
   └─ scraper_service.scrape_evidence() → httpx + BeautifulSoup (4 sources, concurrent)
   └─ update status → "analyzing"       → Upstash Redis cache + MongoDB Atlas
   └─ gemini_service.analyze_claim()    → Gemini API
   └─ update status → "done"            → Upstash Redis cache + MongoDB Atlas
   └─ final write to MongoDB Atlas      → permanent storage

3. SSE stream
   └─ polls Upstash Redis cache every 2s
   └─ emits status_update on each change
   └─ emits result on done/failed
   └─ closes connection
```

---

## Deployment

### Local dev

No local services needed. MongoDB runs on Atlas, Redis runs on Upstash — just run the API and worker directly.

```bash
# Optional: use docker-compose to run API + worker together
docker-compose up
```

### GCP (production)

#### MongoDB — Atlas M0 (always-free tier)

No deployment needed. Your Atlas cluster is already running in the cloud. Make sure the Cloud Run service IP is whitelisted in Atlas **Network Access**, or set `0.0.0.0/0` during development.

#### Upstash Redis — (always-free tier)

No deployment needed. Upstash is fully managed and accessible over HTTPS from anywhere including Cloud Run.

#### FastAPI — Cloud Run

Deployed automatically by GitHub Actions on push to `main`. See `.github/workflows/deploy.yml`.

```bash
# Manual deploy
gcloud run deploy verifai-api \
  --image gcr.io/YOUR_PROJECT/verifai-api:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars MONGODB_URL=mongodb+srv://<user>:<pass>@<cluster>.mongodb.net/verifai
```

#### Worker — Cloud Run Jobs

```bash
gcloud run jobs create verifai-worker \
  --image gcr.io/YOUR_PROJECT/verifai-worker:latest \
  --region us-central1
```

---

## CI/CD

Two GitHub Actions workflows:

### `ci.yml` — runs on every PR

```
Turborepo detects changed packages
  ├─ lint affected apps
  ├─ run affected tests
  └─ type-check shared-types
```

### `deploy.yml` — runs on push to `main`

```
1. Build Docker images (API + worker) in CI — no local Docker needed
2. Push to Google Container Registry
3. Deploy API image to Cloud Run
4. Trigger Cloud Run Job update for worker
```

Turborepo's remote cache means unchanged apps are skipped entirely — builds stay fast as the project grows.

---

## Observability

### OpenTelemetry

Distributed traces span the full request lifecycle — from the HTTP request into FastAPI, through Upstash Redis queue push, to the worker scraping and AI call. Configure the OTLP exporter endpoint in `.env` to send traces to any compatible backend (GCP Trace, Jaeger, etc.).

### Sentry

Error tracking is initialized in:
- **FastAPI** — catches unhandled exceptions, attaches request context
- **Next.js** — client and server-side error capture
- **Expo** — mobile crash reporting

Set `SENTRY_DSN_*` environment variables to enable. Can be left empty in local dev.

---

## Development Notes

### Adding a new scrape target

Add the target URL to the sources list in `app/services/scraper.py`. httpx fetches the page and BeautifulSoup handles the content extraction. Use your browser's dev tools to identify the right HTML selectors for the content you need.

### Shared types

`packages/shared-types` contains Zod schemas that mirror the Pydantic models in `apps/api/app/models/claim.py` exactly. When you change a model, update both files to keep the frontend and backend in sync.

### Turborepo tips

```bash
# Run only the API dev server
npx turbo dev --filter=api

# Build only affected packages since last commit
npx turbo build --filter=[HEAD^1]

# See the task dependency graph
npx turbo graph
```

---

## Roadmap

- [ ] Playwright-based scraping for JavaScript-rendered sources
- [ ] User accounts and saved claim history
- [ ] Public feed of recently fact-checked claims
- [ ] Community upvotes on verdicts
- [ ] Browser extension for one-click fact-checking