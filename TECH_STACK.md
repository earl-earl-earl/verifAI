### 🗄️ Data
| Tech | Role |
|---|---|
| **MongoDB Community** | Self-hosted primary database — claims, reports, sources, users |
| **Motor** | Async MongoDB driver for Python |
| **Redis** | Job queue + result caching |

### ⚙️ Backend
| Tech | Role |
|---|---|
| **FastAPI** | REST API + SSE + WebSocket endpoints |
| **Pydantic v2** | Request/response validation, MongoDB document models |
| **Playwright** | Web scraping worker |
| **Playwright Codegen** | Record scraping scripts visually |

### 🤖 AI
| Tech | Role |
|---|---|
| **Gemini API** | Verdict generation + explanation |

### 📦 Containerization
| Tech | Role |
|---|---|
| **Docker** | CI-only builds + local dev via `docker-compose` |
| **docker-compose** | Local dev — spins up MongoDB + Redis + worker together |

### ☁️ Cloud
| Tech | Role |
|---|---|
| **GCP Cloud Run** | Hosts FastAPI container, scales to zero |
| **GCP Cloud Run Jobs** | On-demand Playwright scraper |
| **GCP Pub/Sub** | Job trigger queue |
| **GCP Container Registry** | Stores Docker images |
| **GCE e2-micro VM** | Runs self-hosted MongoDB 24/7 with persistent disk (free tier) |

### 🌐 Web
| Tech | Role |
|---|---|
| **Next.js** | Web app — dashboard, claim feed, verdicts |
| **Zod** | Schema validation mirroring Pydantic models |

### 📱 Mobile
| Tech | Role |
|---|---|
| **Expo** | Mobile app — share-sheet claim submission |

### 🔁 CI/CD & Monorepo
| Tech | Role |
|---|---|
| **Turborepo** | Monorepo pipelines, smart caching, affected-only builds |
| **GitHub Actions** | Build, test, push images, deploy to Cloud Run |

### 📊 Observability
| Tech | Role |
|---|---|
| **OpenTelemetry** | Distributed tracing across FastAPI + worker |
| **Sentry** | Error tracking for API, web, and mobile |

### 📐 Shared
| Tech | Role |
|---|---|
| **Zod** | Frontend schema validation (`packages/shared-types`) |
| **Pydantic v2** | Backend schema validation, matches Zod schemas 1:1 |

---

### Key architecture note on MongoDB hosting

```
Local dev          →  docker-compose (MongoDB + Redis + worker + FastAPI)
Cloud deploy       →  GCE e2-micro VM (MongoDB in container + persistent disk)
                       ↕
                      Cloud Run (FastAPI) connects via internal GCP VPC
```

The `e2-micro` VM stays within GCP's **always-free tier** — 1 vCPU, 1GB RAM, 30GB persistent disk, which is more than enough for a portfolio project.

---

Ready to update the code? I'll tackle in order: `docker-compose.yml` → `requirements.txt` → MongoDB connection with Motor → updated Pydantic models → updated routers.