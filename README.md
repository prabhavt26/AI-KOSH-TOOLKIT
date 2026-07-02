# AIKosh Dataset Quality Evaluation Toolkit

![AIKosh Logo](https://img.shields.io/badge/AIKosh-Dataset%20Quality-blue?style=for-the-badge)

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen?style=flat-square)](#)
[![Python Version](https://img.shields.io/badge/python-3.10-blue?style=flat-square&logo=python)](backend/requirements.txt)
[![Next.js](https://img.shields.io/badge/Next.js-14-black?style=flat-square&logo=nextdotjs)](#)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-blue?style=flat-square&logo=typescript)](#)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16.x-blue?style=flat-square&logo=postgresql)](#)
[![Celery](https://img.shields.io/badge/Celery-5.4.0-green?style=flat-square&logo=celery)](#)
[![Redis](https://img.shields.io/badge/Redis-7.2-red?style=flat-square&logo=redis)](#)
[![AWS S3](https://img.shields.io/badge/AWS%20S3-Object%20Storage-orange?style=flat-square)](#)

> **A user-facing, browser-first web application for automated MIDAS-grade health dataset quality assessment — with a secure multi-tenant backend, async processing pipeline, and a REST API surface that external platforms (AIKosh) can integrate with programmatically.**

Dataset custodians log in via the web UI, upload health research datasets, and receive structured quality scores across **15 MIDAS 2.0 domains**, a **Composite Quality Index (CQI)**, a **Privacy Risk Score (PRS)**, and a **release classification** (Open / Controlled / Restricted). The AIKosh platform integrates as an external consumer via REST API and receives quality metadata via webhook on assessment completion.

---

### [Quick Start](#8-quick-start) &middot; [API Docs](#12-api-documentation) &middot; [Architecture](#3-system-architecture) &middot; [Implementation Status](#2-current-implementation-status) &middot; [Cheatsheet](#14-common-commands-cheatsheet)

---

## Table of Contents
1. [Overview & Concept](#1-overview--concept)
2. [Current Implementation Status](#2-current-implementation-status)
3. [System Architecture](#3-system-architecture)
4. [Tech Stack](#4-tech-stack)
5. [Security & Authentication](#5-security--authentication)
6. [Living Documentation & Reference Disclaimer](#6-living-documentation--reference-disclaimer)
7. [Prerequisites](#7-prerequisites)
8. [Quick Start](#8-quick-start)
9. [Configuration Reference](#9-configuration-reference)
10. [Development Setup (Without Docker)](#10-development-setup-without-docker)
11. [Database Migrations (Alembic)](#11-database-migrations-alembic)
12. [API Documentation](#12-api-documentation)
13. [Testing](#13-testing)
14. [Common Commands Cheatsheet](#14-common-commands-cheatsheet)
15. [Troubleshooting & FAQ](#15-troubleshooting--faq)
16. [Production Deployment (Kubernetes)](#16-production-deployment-kubernetes)

---

## 1. Overview & Concept

The **AIKosh Dataset Quality Evaluation Toolkit** is a standalone full-stack web application that provides automated quality assessment for health research datasets submitted to the AIKosh platform (IndiaAI Mission).

Users authenticate through the browser UI, upload datasets, fill in a structured metadata form, and receive a comprehensive quality report. The system scores each dataset across **15 MIDAS 2.0 evaluation domains**, computes a normalized **CQI** (Composite Quality Index, 0–100), a **PRS** (Privacy Risk Score, 0–100), and classifies the dataset's release eligibility (Open / Controlled / Restricted). Reports are generated in JSON, HTML, and PDF formats and stored in object storage.

The AIKosh platform integrates as an external consumer — it submits datasets via REST API (using API keys) and receives quality metadata via webhook when assessments complete.

---

## 2. Current Implementation Status

> This table is the authoritative source of what's built and what's planned. Update it whenever a component is completed.

| Component | Status | Notes |
|---|---|---|
| **Auth** (register / login / logout / me) | ✅ Complete | JWT HttpOnly cookies, bcrypt, Redis rate limiting |
| **API key management** (generate / list / revoke) | ✅ Complete | Per-user developer keys, SHA-256 hash storage |
| **Admin user management** (list / suspend / reactivate) | ✅ Complete | Strict privacy boundary — admin cannot see datasets |
| **ORM models** (all 9 tables) | ✅ Complete | `backend/app/models/` |
| **DB schema** (PostgreSQL DDL) | ✅ Complete | `backend/alembic/` |
| **Health endpoint** | ✅ Complete | `GET /api/v1/health` |
| **Frontend** (Login + Register pages) | ✅ Complete | Next.js auth layout and views |
| **Assessment submission** | ✅ Complete | Full schema intake and S3 key validation |
| **Pre-signed S3 upload URL** (`POST /assess/upload-url`) | ✅ Complete | Client direct uploads to AWS S3 bucket |
| **Celery assessment pipeline** (13 steps) | ✅ Complete | Async pipeline with state machine, audit log triggers |
| **Dataset profiler** | ✅ Complete | Real pandas-based PII, completeness, and size scanner |
| **15 Domain scorers** | ✅ Complete | Confirmed score criteria evaluation from YAML configuration |
| **CQI engine** | ✅ Complete | Composite Quality Index calculations (0-100) |
| **PRS engine** | ✅ Complete | Privacy Risk Score and baseline/stigma adjustments |
| **Release classifier** | ✅ Complete | Real CQI x PRS release eligibility matrix |
| **Report generator** (JSON + HTML + PDF) | ✅ Complete | Pre-signed URL distribution of JSON/HTML/PDF templates |
| **S3 client wrapper** | ✅ Complete | `backend/app/storage/s3_client.py` |
| **AIKosh webhook sender** | ✅ Complete | Webhook callbacks dispatch on completion |
| **Audit logger** | ✅ Complete | Strict append-only postgres audit ledger |
| **Frontend** (Upload, Dashboard, Report pages) | ✅ Complete | 8-step metadata questionnaire wizard, Recharts, gauges |
| **Frontend** (Admin page) | ✅ Complete | Admin moderation panel |
| **Frontend URL routing** | ✅ Complete | Next.js 14 App Router paths |
| **Next.js + TypeScript migration** | ✅ Complete | 100% complete Next.js port |

---

## 3. System Architecture

### Data Flow

```
Browser User ──────→ Next.js Frontend (port 3000)
                              │
                              │ HTTP + HttpOnly session cookie
                              ▼
AIKosh Platform ───────────→ FastAPI API (port 8000)
                              │
               ┌──────────────┼──────────────┐
               │              │               │
          SQLAlchemy       Redis           boto3 (S3)
          (async)       (Celery broker)       │
               │              │               ▼
           PostgreSQL       Celery          AWS S3
           (port 5432)      Workers
                              │
                 ┌────────────┴────────────┐
                 │     13-step pipeline     │
                 │  Profile → Score ×15     │
                 │  CQI / PRS / Release     │
                 │  Report → Webhook        │
                 └──────────────────────────┘
                              │
                              └──→ Webhook POST → AIKosh
```

### Repository Structure

```
.
├── AGENTS.md                # ← Read first. AI agent orientation guide.
├── backend/
│   ├── alembic/             # Database migrations
│   ├── app/
│   │   ├── api/v1/          # FastAPI routers (auth, admin, assess, reports, health)
│   │   ├── models/          # SQLAlchemy ORM models (9 tables)
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── engine/          # Profiler, domain scorers, CQI/PRS engines (partly stub)
│   │   ├── worker/          # Celery task definitions
│   │   ├── config.py        # Pydantic Settings (env vars)
│   │   ├── database.py      # Async SQLAlchemy engine + session
│   │   └── main.py          # FastAPI app entry point
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                # Currently React 18 + Vite (Next.js migration planned)
│   ├── src/
│   │   ├── pages/           # LoginPage, RegisterPage, UploadPage, DashboardPage, ReportPage
│   │   ├── api/client.js    # Typed API client (fetch + credentials)
│   │   └── App.jsx          # Auth-gated router (currentView state)
│   ├── Dockerfile
│   └── package.json
├── k8s/                     # Kubernetes production manifests
├── docs/
│   ├── PRD_AIKosh_Dataset_Quality_Toolkit.md  # Product requirements
│   ├── TDD_AIKosh_Dataset_Quality_Toolkit.md  # Technical architecture
│   └── OpenAPI.md                             # Full API contract
└── docker-compose.yml       # 7-service local dev stack
```

---

## 4. Tech Stack

### Frontend (Target — Next.js migration planned)

| Layer | Technology | Purpose |
|---|---|---|
| Framework | **Next.js 14** (App Router) | File-based routing, auth layouts, loading/error boundaries per route |
| Language | **TypeScript 5** | Type safety for complex domain score objects and API contracts |
| Styling | **Tailwind CSS** | Utility-first, consistent design tokens |
| Components | **shadcn/ui** | Pre-built accessible components (Table, Badge, Form, Dialog); owned code |
| Data Fetching | **TanStack Query v5** | Assessment status polling, caching, loading/error states |
| Forms | **React Hook Form + Zod** | 20+ field metadata form; Zod schema mirrors backend Pydantic model |
| Global State | **Zustand** | Auth user state, minimal boilerplate |
| Charts | **Recharts** | Radar chart (15 domains), radial gauge (CQI/PRS) |

### Backend

| Layer | Technology | Purpose |
|---|---|---|
| API | **FastAPI + Uvicorn** | Async API, auto-OpenAPI, Pydantic validation |
| Task Queue | **Celery 5.4** | Long-running assessment jobs; parallel domain scoring via `group` |
| Broker | **Redis 7.2** | Celery broker + result backend + rate limiting store |
| ORM | **SQLAlchemy 2.0 async** | Async PostgreSQL access |
| Database | **PostgreSQL 16** | JSONB for evidence/gaps; ACID for audit logs |
| Migrations | **Alembic** | Version-controlled schema changes |
| Config | **Pydantic Settings v2** | Type-validated env vars |
| Logging | **structlog** | Structured JSON logs for Celery worker tracing |
| Auth | **pyjwt + passlib[bcrypt]** | JWT session cookies + bcrypt password hashing |
| Profiling | **pandas 2.2 + pyarrow** | Dataset statistical profiling |
| Reports | **Jinja2 + WeasyPrint** | HTML→PDF report generation inside Docker |
| S3 Client | **boto3** | AWS S3 Object Storage (both dev and prod) |

### Infrastructure

| Layer | Technology |
|---|---|
| Dev Orchestration | Docker Compose (7 services) |
| Production | Kubernetes (`k8s/` manifests) |
| Object Storage | AWS S3 Object Storage |
| Worker Monitoring | Flower (port 5555) |

---

## 5. Security & Authentication

The system uses a **Dual-Authentication Model** to support both secure human browser interactions and programmatic machine integrations:

- **User Session Authentication (Browser UI):** JWT stored in a secure, `HttpOnly`, `Secure`, `SameSite=Lax` cookie named `session_token`. Sessions are persistent (30 days).
- **Developer API Key Authentication (Machine Integrations):** API keys passed as Bearer tokens in the `Authorization` header (`Authorization: Bearer tkt_live_...`), validated against SHA-256 database hashes. Keys are issued per-user and managed via the UI or API.
- **Role-Based Access:** `user` (submitter), `reviewer` (+ audit logs), `admin` (user management only — **cannot** view datasets or reports).
- **Tenant Data Isolation:** Users can only access their own assessments and files.
- **Manual File Deletion:** Dataset files are retained in AWS S3 permanently until the user explicitly deletes them via the UI or API.

---

## 6. Living Documentation & Reference Disclaimer

> [!IMPORTANT]
> The architectural design patterns, dataset questionnaires, and schemas in the **[docs/](docs/)** folder are **living reference guidelines** that represent target specifications. The active codebase is the source of truth for what is currently implemented. The [Current Implementation Status](#2-current-implementation-status) table above reflects the real state.

---

## 7. Prerequisites

- **Docker Engine:** `20.10.x` or newer (Compose V2)
- **Python:** `3.10.x` (for local backend development)
- **Node.js:** `18.x` LTS (for local frontend development)
- **PostgreSQL Client (`psql`):** `16.x` (optional, for SQL debugging)

---

## 8. Quick Start

Deploy the entire stack locally in 3 steps:

```bash
# 1. Clone the repository and set up environment configurations
cp .env.example .env

# 2. Build and start all container services in the background
docker compose up --build -d

# 3. Apply database migrations to PostgreSQL
docker compose exec backend alembic upgrade head
```

Services available at:
- **Web UI (Frontend):** http://localhost:3000
- **FastAPI OpenAPI Docs:** http://localhost:8000/docs

- **Flower Celery Monitoring:** http://localhost:5555

---

## 9. Configuration Reference

<details>
<summary><b>Click to expand Environment Variables Reference...</b></summary>

All configuration is loaded from the root `.env` file via Pydantic Settings.

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://toolkit:password@localhost:5432/toolkit_db` | Async PostgreSQL connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis broker URL for Celery |
| `S3_ENDPOINT_URL` | — | Endpoint URL (optional, left blank for AWS S3) |
| `S3_BUCKET_NAME` | `aikosh-datasets` | AWS S3 bucket name |
| `S3_ACCESS_KEY` | — | AWS access key ID |
| `S3_SECRET_KEY` | — | AWS secret access key |
| `S3_REGION` | `ap-south-1` | S3 region |
| `AIKOSH_WEBHOOK_URL` | — | AIKosh webhook endpoint for quality metadata delivery |
| `AIKOSH_WEBHOOK_SECRET` | — | Bearer token for AIKosh webhook authentication |
| `MAX_FILE_SIZE_BYTES` | `5368709120` | Max file upload size (5GB) |
| `PROFILING_SAMPLE_ROWS` | `100000` | Rows to sample for large dataset profiling |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed frontend origins (credential-aware CORS) |
| `JWT_SECRET` | — | Secret key for JWT signing |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `JWT_EXPIRY_MINUTES` | `43200` | Session duration (30 days) |
| `ENVIRONMENT` | `development` | `development` / `staging` / `production` |

</details>

---

## 10. Development Setup (Without Docker)

### A. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux/Mac

pip install -r requirements.txt

# Ensure PostgreSQL is running on localhost:5432 with toolkit_db database
alembic upgrade head

uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### B. Frontend (Current — React + Vite)

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

> **Note:** The frontend will be migrated to Next.js + TypeScript + Tailwind CSS. When that migration completes, the dev server command remains `npm run dev` but the env var changes from `VITE_API_URL` to `NEXT_PUBLIC_API_URL`.

---

## 11. Database Migrations (Alembic)

```bash
# Apply all pending migrations
docker compose exec backend alembic upgrade head

# Revert the last migration
docker compose exec backend alembic downgrade -1

# Generate a new migration from model changes
docker compose exec backend alembic revision --autogenerate -m "description_of_change"
```

---

## 12. API Documentation

- **Swagger UI (Interactive):** http://localhost:8000/docs
- **ReDoc (Reading mode):** http://localhost:8000/redoc
- **Full API Contract:** [docs/OpenAPI.md](docs/OpenAPI.md)

---

## 13. Testing

```bash
docker compose exec backend pytest
```

Test coverage targets: scoring formulas, PRS calculations, domain scorer unit tests, API endpoint contract tests, and end-to-end assessment flow integration tests.

---

## 14. Common Commands Cheatsheet

| Command | Action |
|---|---|
| `docker compose up -d` | Start all services in the background |
| `docker compose down` | Stop all containers |
| `docker compose logs -f backend` | Stream FastAPI logs |
| `docker compose logs -f worker_assessment` | Stream Celery assessment worker logs |
| `docker compose exec backend alembic upgrade head` | Run all DB migrations |
| `docker compose exec backend alembic downgrade -1` | Rollback last migration |
| `docker compose exec backend pytest` | Run backend tests |
| `docker compose exec postgres psql -U toolkit -d toolkit_db` | Open PostgreSQL shell |
| `docker compose restart backend` | Restart the API container |

---

## 15. Troubleshooting & FAQ

#### Q1: "port 5432 is already in use" on startup
**Reason:** Local PostgreSQL instance is running on the host.
**Fix:** Stop your host PostgreSQL service, or modify the port mapping in `docker-compose.yml`.

#### Q2: Alembic "connection refused" or "database does not exist"
**Reason:** PostgreSQL container takes a few seconds to become ready.
**Fix:** Wait 10 seconds after `docker compose up`, then re-run `alembic upgrade head`.

#### Q3: S3 bucket error "does not exist"
**Reason:** The configured bucket does not exist or credentials lack permissions to create/access it.
**Fix:** Ensure `S3_BUCKET_NAME` in `.env` matches the actual S3 bucket name, and S3 credentials have the necessary permissions. The Celery workers attempt to auto-create the bucket on first use if it is missing.

#### Q4: CORS errors on login from the frontend
**Reason:** `allow_credentials=True` requires explicit origin in `CORS_ORIGINS` — not `"*"`.
**Fix:** Add `http://localhost:3000` to the `CORS_ORIGINS` list in your `.env`.

#### Q5: Assessment stuck in "queued" status
**Reason:** Celery workers are not running, or the pipeline is the current stub.
**Fix:** Check `docker compose logs worker_assessment`. The `run_assessment` task is currently a stub — full pipeline implementation is pending (see [Implementation Status](#2-current-implementation-status)).

---

## 16. Production Deployment (Kubernetes)

Production manifests are in the **[k8s/](k8s/)** directory, targeting namespace `aikosh-quality-toolkit`.

```bash
# 1. Apply stateful services
kubectl apply -f k8s/postgres-statefulset.yaml
kubectl apply -f k8s/redis-deployment.yaml

# 2. Deploy API and workers
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/worker-deployment.yaml

# 3. Configure ingress and autoscaling
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/worker-hpa.yaml
```

Assessment workers auto-scale from 3 to 20 replicas via HPA based on Celery queue depth.

---

**Document History**

| Version | Date | Notes |
|---|---|---|
| 1.0 | June 18, 2026 | Initial README |
| 1.1 | June 24, 2026 | Realigned to full-stack app architecture. Added implementation status table, updated tech stack to Next.js + TypeScript + Tailwind (target), fixed env vars, added AGENTS.md reference. |
