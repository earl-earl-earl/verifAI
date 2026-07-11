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

---

## Overview

verifAI is a full-stack portfolio project demonstrating end-to-end system design across backend, AI, mobile, web, infrastructure, and observability. Every technology in the stack is load-bearing — nothing is included for show.

**What it does:**
1. User submits a claim via the web or mobile app
2. API queues a scraping job to Redis
3. A Playwright worker scrapes trusted sources (Reuters, AP News, Snopes, PolitiFact)
4. Gemini AI analyzes the claim against the scraped evidence
5. A verdict (`true` / `false` / `misleading` / `unverifiable`) is returned with a confidence score and explanation
6. Results are streamed back to the client in real time via SSE or WebSocket

---

## Tech Stack

### Backend
| Technology | Purpose |
|---|---|
| **FastAPI** | REST API, SSE streaming, WebSocket endpoints |
| **Pydantic v2** | Request/response validation and MongoDB document models |
| **Motor** | Async MongoDB driver |
| **Playwright** | Headless browser scraping worker |
| **Playwright Codegen** | Visual script recording for new scrape targets |

### AI
| Technology | Purpose |
|---|---|
| **Gemini API** (`gemini-1.5-flash`) | Verdict generation, confidence scoring, explanation |

### Data
| Technology | Purpose |
|---|---|
| **MongoDB Community** | Self-hosted primary database — claims, reports, sources, users |
| **Redis** | Job queue (scrape jobs) + result cache (TTL-based) |

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
| **docker-compose** | Local dev environment — MongoDB + Redis + worker + API |

### Cloud (GCP)
| Technology | Purpose |
|---|---|
| **Cloud Run** | Hosts FastAPI container, scales to zero (free when idle) |
| **Cloud Run Jobs** | On-demand Playwright scraper execution |
| **Pub/Sub** | Job trigger queue between API and scraper |
| **Container Registry** | Stores Docker images built by CI |
| **GCE e2-micro VM** | Runs self-hosted MongoDB 24/7 with persistent disk |

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
│    Redis    │      │    MongoDB          │
│  job queue  │      │  (GCE e2-micro VM)  │
│  + cache    │      │  self-hosted        │
└──────┬──────┘      └─────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│         GCP CLOUD RUN JOB                │
│         Playwright Worker                │
│  1. Scrape Reuters, AP, Snopes, Politifact│
│  2. Call Gemini API for verdict          │
│  3. Write result back to MongoDB + cache │
└──────────────────────────────────────────┘
```

### Request lifecycle

```
Client
  │
  ├─ POST /api/v1/claims          → API creates report (status: pending)
  │                               → pushes job to Redis queue
  │                               ← returns { id, status: "pending" }
  │
  ├─ GET /api/v1/claims/:id/stream  (SSE)
  │     ↕ polls cache every 2s
  │     ← event: status_update { status: "scraping" }
  │     ← event: status_update { status: "analyzing" }
  │     ← event: result         { verdict, confidence, sources, explanation }
  │
Worker (separate process)
  ├─ brpop Redis queue
  ├─ Playwright scrapes 4 sources concurrently
  ├─ Gemini API returns structured verdict
  └─ Writes final report to MongoDB + updates Redis cache
```

---

## Project Structure

```
factcheck/
├── apps/
│   ├── api/                        # FastAPI backend
│   │   ├── app/
│   │   │   ├── core/
│   │   │   │   ├── config.py       # pydantic-settings, all env vars
│   │   │   │   ├── redis.py        # async Redis client singleton
│   │   │   │   └── database.py     # Motor MongoDB client singleton
│   │   │   ├── models/
│   │   │   │   └── claim.py        # Pydantic v2 models (ClaimReport, Source, etc.)
│   │   │   ├── routers/
│   │   │   │   ├── claims.py       # POST /claims, GET /claims/:id, SSE stream
│   │   │   │   └── health.py       # GET /health, GET /health/ready
│   │   │   ├── services/
│   │   │   │   ├── cache.py        # Redis read/write for reports
│   │   │   │   ├── queue.py        # Redis job push/pop
│   │   │   │   ├── scraper.py      # Playwright scraping service
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
├── docker-compose.yml              # Local dev: MongoDB + Redis + API + worker
├── turbo.json                      # Turborepo pipeline config
├── package.json                    # Root workspace config
└── .gitignore
```

---

## Getting Started

### Prerequisites

- Node.js 20+
- Python 3.11+
- Docker + Docker Compose (for local services only — not for building)
- A Gemini API key (free at [aistudio.google.com](https://aistudio.google.com))

### 1. Clone and install

```bash
git clone https://github.com/yourusername/verifai.git
cd verifai
npm install          # installs all JS workspaces via Turborepo
```

### 2. Set up Python environment

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

### 3. Start local services (MongoDB + Redis)

```bash
# From the project root — Docker only used here, not for building
docker-compose up -d mongo redis
```

### 4. Configure environment variables

```bash
cp .env.example .env
# Fill in GEMINI_API_KEY and any other values
```

### 5. Run the API

```bash
cd apps/api
uvicorn app.main:app --reload --port 8000
```

### 6. Run the worker (separate terminal)

```bash
cd apps/api
python -m app.workers.scrape_worker
```

### 7. Run the web app

```bash
cd apps/web
npm run dev        # or from root: npx turbo dev --filter=web
```

### 8. Run the mobile app

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

# MongoDB (self-hosted)
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=verifai

# Redis
REDIS_URL=redis://localhost:6379
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

Readiness check — verifies Redis connectivity and returns queue length.

---

## Data Flow

```
1. POST /claims
   └─ Create ClaimReport (status: pending)
   └─ cache_service.set_report()        → Redis (TTL: 1hr)
   └─ queue_service.push_scrape_job()   → Redis list (LPUSH)
   └─ Return { id, status: pending }

2. Worker loop (brpop)
   └─ pop job from Redis
   └─ update status → "scraping"        → Redis cache
   └─ scraper_service.scrape_evidence() → Playwright (4 sources, concurrent)
   └─ update status → "analyzing"       → Redis cache + MongoDB
   └─ gemini_service.analyze_claim()    → Gemini API
   └─ update status → "done"            → Redis cache + MongoDB
   └─ final write to MongoDB            → permanent storage

3. SSE stream
   └─ polls Redis cache every 2s
   └─ emits status_update on each change
   └─ emits result on done/failed
   └─ closes connection
```

---

## Deployment

### Local services only (no cloud account needed)

```bash
docker-compose up
```

Starts: MongoDB on `27017`, Redis on `6379`, FastAPI on `8000`, worker process.

### GCP (production)

#### MongoDB — GCE e2-micro VM (always-free tier)

```bash
# Create VM
gcloud compute instances create verifai-mongo \
  --machine-type=e2-micro \
  --zone=us-central1-a \
  --boot-disk-size=30GB

# SSH in and run MongoDB
docker run -d \
  --name mongodb \
  --restart unless-stopped \
  -p 27017:27017 \
  -v /data/db:/data/db \
  mongo:7
```

#### FastAPI — Cloud Run

Deployed automatically by GitHub Actions on push to `main`. See `.github/workflows/deploy.yml`.

```bash
# Manual deploy
gcloud run deploy verifai-api \
  --image gcr.io/YOUR_PROJECT/verifai-api:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars MONGODB_URL=mongodb://MONGO_VM_IP:27017
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

Distributed traces span the full request lifecycle — from the HTTP request into FastAPI, through Redis queue push, to the worker scraping and AI call. Configure the OTLP exporter endpoint in `.env` to send traces to any compatible backend (GCP Trace, Jaeger, etc.).

### Sentry

Error tracking is initialized in:
- **FastAPI** — catches unhandled exceptions, attaches request context
- **Next.js** — client and server-side error capture
- **Expo** — mobile crash reporting

Set `SENTRY_DSN_*` environment variables to enable. Can be left empty in local dev.

---

## Development Notes

### Adding a new scrape target

Use Playwright Codegen to record a scraping script against any site:

```bash
cd apps/api
playwright codegen https://www.snopes.com/search/target-topic
```

Copy the generated selectors into `app/services/scraper.py`.

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