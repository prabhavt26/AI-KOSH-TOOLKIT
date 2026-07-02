# Security Audit Checklist
# AIKosh Dataset Quality Evaluation Toolkit

**Document Version:** 1.0  
**Status:** Active  
**Last Updated:** June 25, 2026  
**Classification:** Internal Working Document  
**Base Documents:** PRD v1.1, TDD v1.1, OpenAPI v1.1, Questionnaire v1.1, AGENTS.md v1.1

---

## Table of Contents

1. [Threat Model (STRIDE per Layer)](#1-threat-model-stride-per-layer)
2. [Automated Security Testing Matrix](#2-automated-security-testing-matrix)
3. [Manual Security Review Checklist](#3-manual-security-review-checklist)
4. [CI/CD Pipeline Integration](#4-cicd-pipeline-integration)
5. [Remediation Priority Matrix](#5-remediation-priority-matrix)
6. [Alignment with OWASP Standards](#6-alignment-with-owasp-standards)
7. [Hardening Guides by Component](#7-hardening-guides-by-component)
8. [Appendix — Mapped Documentation References](#8-appendix--mapped-documentation-references)

---

## 1. Threat Model (STRIDE per Layer)

> STRIDE categories: **S**poofing | **T**ampering | **R**epudiation | **I**nformation Disclosure | **D**enial of Service | **E**levation of Privilege

---

### 1.1 Frontend (Next.js 14 App Router — `frontend/app/`)

| Component | STRIDE Category | Threat | Existing Mitigation | Gap / Action Needed |
|---|---|---|---|---|
| Login page (`/login/page.tsx`) | Spoofing | Attacker phishes users to a lookalike login page and harvests credentials | HTTPS enforced at K8s Ingress (TLS via cert-manager) | No HSTS header set; add `Strict-Transport-Security: max-age=31536000; includeSubDomains` in `next.config.ts` headers |
| Auth store (`frontend/stores/auth.ts`) | Information Disclosure | Session token leaked to JavaScript via localStorage or window object | Tokens stored in HttpOnly cookie (server-set); React state holds only non-sensitive user metadata | Verify no `dangerouslySetInnerHTML` usage; confirm token is never copied to `localStorage` |
| API client (`frontend/lib/api/client.ts`) | Spoofing | API calls made to wrong backend origin (DNS hijack, open redirect) | CORS restricted to `settings.CORS_ORIGINS` | No Subresource Integrity (SRI) on scripts; enforce `credentials: 'include'` on all fetch calls |
| TanStack Query cache (`hooks/use-assessment.ts`) | Information Disclosure | Cached assessment results (domain scores, PRS) readable by XSS payload injected via malicious metadata field | React auto-escapes rendered values | Ensure no `dangerouslySetInnerHTML` wraps any metadata string from API responses; add CSP header blocking inline scripts |
| Result display (`components/domain-score-table.tsx`) | Tampering | Reflected XSS via `rationale`, `evidence_items`, or `gaps` strings echoed from assessment results | React JSX escapes by default | Add `Content-Security-Policy: default-src 'self'; script-src 'self'` in `next.config.ts` |
| Report download (`/report/[id]/page.tsx`) | Information Disclosure | Open redirect — attacker crafts URL that redirects user to arbitrary S3-lookalike URL | Pre-signed URLs generated server-side with 24h expiry | Validate redirect target domain at frontend before following; server already restricts to toolkit S3 bucket |
| Admin panel (`/admin/page.tsx`) | Elevation of Privilege | Non-admin user navigates directly to `/admin` and sees user management UI | Role check in `(app)/layout.tsx` redirects unauthenticated users | Verify that admin route group enforces role=admin check, not just `is_active`; add server-side role assertion |
| Registration form (`/register/page.tsx`) | Denial of Service | Bot submits thousands of registrations exhausting DB user table | IP-rate-limit 5/min via Redis (TDD §20) | No CAPTCHA on registration; consider adding for public-facing deployment |
| Next.js headers config (`next.config.ts`) | Information Disclosure | Default Next.js `X-Powered-By: Next.js` reveals framework version | Not mitigated | Add `poweredByHeader: false` in `next.config.ts` |

---

### 1.2 API Layer (FastAPI — `backend/app/`)

| Component | STRIDE Category | Threat | Existing Mitigation | Gap / Action Needed |
|---|---|---|---|---|
| `main.py` — CORS middleware | Information Disclosure | CORS wildcard exposes API to any origin | `settings.CORS_ORIGINS` restrict to configured origins; `allow_credentials=True` requires explicit origin | Verify `CORS_ORIGINS` never set to `["*"]` in any environment; add test in `backend/tests/test_cors.py` |
| `main.py` — middleware stack | Information Disclosure | Response headers reveal `Server: uvicorn`, FastAPI version, internal paths | None currently | Add `SecurityHeadersMiddleware` setting `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Strict-Transport-Security`, `Content-Security-Policy` |
| `api/v1/auth.py:61-70` — cookie set | Spoofing | `secure=False` hardcoded — cookie transmitted over HTTP in development and potentially production if env var not toggled | Comment says "Set to True in production with HTTPS" | Replace with `secure=settings.ENVIRONMENT == "production"` to prevent accidental plaintext transmission |
| `api/deps.py` — `get_current_user()` | Spoofing | JWT `alg: none` attack — attacker crafts unsigned token if library accepts "none" algorithm | `pyjwt 2.8.x` — must pass `algorithms=["HS256"]` explicitly | Verify `jwt.decode()` call in `deps.py` passes `algorithms=["HS256"]` and NOT `algorithms=jwt.algorithms.get_default_algorithms()` |
| `api/v1/assess.py` — file upload | Tampering | Malicious file (polyglot, zip bomb, executable) uploaded bypassing extension check | MIME + magic bytes check documented in TDD §20 | No automated test for magic bytes validation exists; add `backend/tests/test_file_upload_security.py` |
| `api/v1/assess.py` — upload-url endpoint | Elevation of Privilege | Pre-signed URL generated for a path the user does not own; user uploads to another user's assessment S3 key | assessment_id embedded in key path, generated server-side | Verify S3 key prefix includes authenticated `user_id`, not only `assessment_id` |
| `api/v1/assess/{assessment_id}` — GET | Elevation of Privilege (BOLA) | User A queries User B's assessment_id and receives results | BOLA enforced — test in `backend/tests/test_auth_bola.py` checks User A → 403 | Confirm check is in DB query (not just response serializer) to prevent timing side-channel |
| `api/v1/assess/{assessment_id}/report` | Information Disclosure | 302 redirect to pre-signed URL — URL logged in browser history, proxy logs, Referer headers | 24h expiry on pre-signed URLs | Add `Cache-Control: no-store` to the 302 response to suppress caching; test in `backend/tests/test_s3_security.py` |
| `api/v1/health` — GET | Information Disclosure | Health endpoint leaks internal component topology (postgres ok, redis ok, S3 ok) and version string | No auth required by design (liveness probe) | Expose only `{"status": "healthy"}` to public; return full dependency map only to authenticated callers from internal cluster network |
| `api/v1/auth/register` | Denial of Service | Email enumeration via timing attack — response time differs when email exists vs. not | Not documented | Use constant-time comparison; return identical response for "email already registered" vs success to prevent enumeration |
| Request body parsing | Denial of Service | Attacker sends enormous JSON body to non-upload endpoints causing OOM | FastAPI has no default body size limit other than ASGI max | Add body size limiter middleware for non-upload endpoints (e.g., 1MB cap on `/api/v1/auth/register`, `/api/v1/assess`) |
| Swagger UI (`/docs`) | Information Disclosure | Interactive API docs expose full API surface to unauthenticated users in production | Not addressed | Set `docs_url=None, redoc_url=None` when `settings.ENVIRONMENT == "production"` |
| `integration/aikosh_webhook.py` | SSRF | Attacker provides malicious `webhook_url` in `MetadataForm` that resolves to internal service (e.g., Redis, Postgres metadata URL) | `webhook_url` is optional field in MetadataForm | Add allowlist/denylist validation in `aikosh_webhook.py` blocking RFC-1918 addresses, localhost, link-local; test in `backend/tests/test_webhook_retry.py` |

---

### 1.3 Worker Layer (Celery — `backend/app/worker/`)

| Component | STRIDE Category | Threat | Existing Mitigation | Gap / Action Needed |
|---|---|---|---|---|
| `worker/tasks.py` — `run_assessment` task | Tampering | Task payload in Redis is tampered (assessment_id swapped), causing worker to process wrong file | `task_acks_late=True` prevents replay after failure; Celery uses JSON serializer | Redis has no password by default in `docker-compose.yml`; add `requirepass` immediately; task payloads are not signed |
| `worker/tasks.py` — temp directory | Information Disclosure | Worker writes dataset to a shared temp directory accessible by other processes or containers | "Unique temp dir per Celery task" — TDD §20 | Verify implementation uses `tempfile.mkdtemp()` (not `/tmp/` directly); add cleanup in `finally` block |
| `engine/profiler/identifier_scan.py` — PII scan | Repudiation | Profiler scans dataset but does not record findings in audit log — attacker claims PII was present/absent | Audit log records `profiling_complete` event with `pii_detected` flag | Verify `event_detail` in `audit_logs` includes full PII scan result object, not just boolean |
| `engine/domains/` — 15 domain scorers | Denial of Service | Single malformed dataset causes all 15 parallel Celery tasks to hang, exhausting worker pool | `task_soft_time_limit=300s`, `task_time_limit=360s` terminate runaway tasks | If all workers in `assessment` queue are blocked, new submissions queue indefinitely; HPA auto-scales but needs Redis queue depth metric — verify `celery_queue_length` metric is exported to Prometheus |
| `worker/tasks.py` — `send_webhook` task | Repudiation | Webhook fires but response not logged; AIKosh denies receiving it | `audit_event("aikosh_webhook_sent", {"status_code": ...})` and `audit_event("aikosh_webhook_failed", ...)` both recorded | Verify `audit_logs` entry includes HTTP response body (truncated) for non-200 responses |
| Report generation (`reports/pdf_renderer.py`) | Denial of Service | WeasyPrint renders a crafted HTML file with infinite loops or huge SVGs from metadata inputs | `task_time_limit=360s` kills the worker | WeasyPrint has known DoS vectors via complex CSS; keep metadata field values short (enforce maxLength in Pydantic schema); sandbox PDF generation |
| `reports/templates/quality_report.html` — Jinja2 | Tampering | SSTI (Server-Side Template Injection) if user input is passed unsanitized to `template.render()` | Jinja2 auto-escapes HTML when using `{{ var }}` syntax | Verify `Environment(autoescape=True)` is set in `reports/generator.py`; grep for `{{ var | safe }}` usage which bypasses escaping |

---

### 1.4 Database Layer (PostgreSQL 16 — `backend/app/models/`)

| Component | STRIDE Category | Threat | Existing Mitigation | Gap / Action Needed |
|---|---|---|---|---|
| `models/assessment.py` — queries | Tampering (SQLi) | SQL injection via unsanitized user input in query filters | SQLAlchemy ORM parameterized queries throughout; no raw SQL documented | Add automated check: `grep -rn "text(" backend/app/models/` to find any raw SQL; add `backend/tests/test_sql_injection.py` |
| `audit_logs` table | Tampering | Attacker with DB access deletes audit log rows to cover tracks | `CREATE RULE no_delete_audit AS ON DELETE TO audit_logs DO INSTEAD NOTHING` | Rule prevents delete via SQL but not via `TRUNCATE` — add `RULE no_truncate_audit` or use `ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY` with no delete policy for app role |
| Connection credentials in `settings.DATABASE_URL` | Information Disclosure | DB credentials leaked via environment variable in container inspect, logs, or crash dumps | Pydantic Settings loads from `.env` file; secret not in code | `.env.example` in TDD §21 shows plaintext password — production must use K8s Secret mounted as env var, never a file committed to git |
| `dataset_profiles.profile_json` JSONB column | Information Disclosure | Profile JSON contains column names, sample statistics that could reveal dataset content | Only statistics stored, no raw data per TDD §20 | Verify `profiler.py` never includes raw cell values, only aggregates; add review gate in code review checklist |
| Single DB user for all services | Elevation of Privilege | If API is compromised, attacker has same DB privileges as worker (write to all tables) | Not mitigated — single connection pool shared | Create `toolkit_api` (SELECT/INSERT on assessments, metadata, domain_scores) and `toolkit_worker` (INSERT on results, profiles) separate roles; principle of least privilege |
| PostgreSQL version | Elevation of Privilege | CVEs in PostgreSQL 16.x | `postgres:16-alpine` image; `pip-audit` for Python only | Container scanning (Trivy) must include postgres image; add to CI nightly scan |

---

### 1.5 Object Storage (AWS S3 — `backend/app/storage/s3_client.py`)

| Component | STRIDE Category | Threat | Existing Mitigation | Gap / Action Needed |
|---|---|---|---|---|
| `uploads/` prefix — dataset files | Information Disclosure | Attacker guesses or enumerates S3 object keys and accesses datasets directly without authentication | Pre-signed URLs only; bucket not publicly readable per TDD §7 | Verify `s3_client.py` does not use `ACL='public-read'` on any `put_object` call; add `backend/tests/test_s3_security.py` to verify expired URL returns 403 |
| `reports/` prefix — PDF/HTML/JSON reports | Information Disclosure | 24h pre-signed report URL shared or intercepted; report accessed after intended window | 24h expiry on `generate_presigned_url()` | No mechanism to revoke a pre-signed URL before expiry; document this limitation and ensure reports contain no data beyond what the caller already saw |
| AWS S3 credentials | Information Disclosure | Credentials in local configurations committed to git | `.env.example` shows placeholder; `.env` is gitignored | Ensure that `S3_ACCESS_KEY` and `S3_SECRET_KEY` are not hardcoded in files committed to git; use Kubernetes Secrets in production; scan git history with TruffleHog |
| Pre-signed upload URL (`POST /api/v1/assess/upload-url`) | Elevation of Privilege | Pre-signed upload URL allows PUT of any content type/size to the S3 path — attacker uploads malware | URL tied to specific object key; file validated by profiler after upload | Currently `POST /api/v1/assess/upload-url` generates URL without file size constraint; S3 `PutObject` pre-signed URL does not enforce size limit — add `ContentLengthRange` condition in `generate_presigned_post()` or switch to `generate_presigned_post` which supports conditions |
| Multipart upload (current `multipart/form-data` path) | Denial of Service | Client sends 5GB file via multipart in a single request body, OOM'ing the API worker | `MAX_FILE_SIZE_BYTES=5_368_709_120` documented | Current implementation accepts `multipart/form-data` directly (OpenAPI §7.2 mismatch note) — this means the file passes through the API process memory before reaching S3; pre-signed URL migration resolves this |
| S3 bucket versioning | Denial of Service | Attacker with storage write access overwrites report files, destroying assessment evidence | Not documented as enabled | Enable AWS S3 bucket versioning on `reports/` prefix to prevent overwrite-based evidence destruction |

---

### 1.6 Message Broker (Redis 7.2 — `backend/app/worker/celery_app.py`)

| Component | STRIDE Category | Threat | Existing Mitigation | Gap / Action Needed |
|---|---|---|---|---|
| Redis with no password | Spoofing | Any process on the Docker network or K8s cluster can connect to Redis port 6379 and read/inject Celery task messages | Network isolation via Docker compose internal network | `docker-compose.yml` in TDD §22.1 does NOT show `requirepass` in Redis command; add `command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}` |
| Celery task messages | Tampering | Task JSON payload (`{"assessment_id": "..."}`) is readable in Redis; attacker with Redis access can inject a fake task | `task_acks_late=True` prevents re-queue but not injection | Consider adding HMAC signature to task payloads; at minimum enforce Redis ACL so only `celery_user` can `RPUSH`/`LPOP` on task queues |
| Redis as Celery result backend | Information Disclosure | Task results (domain scores, error tracebacks) stored in Redis result keys accessible to anyone with Redis access | Redis result TTL (default 86400s) limits exposure window | Add `result_expires=3600` in `celery_app.conf.update()` to limit how long results sit in Redis; ensure Redis password required |
| Redis rate-limit counters | Tampering | Attacker with Redis access resets rate-limit counters (`FLUSHDB`), bypassing login rate limiting | Not mitigated | Add `rename-command FLUSHALL ""` and `rename-command FLUSHDB ""` in `redis.conf`; use Redis ACL to restrict app user from these commands |
| Flower monitoring (`port 5555`) | Information Disclosure | Flower exposes all task arguments (including `assessment_id`) and worker state without authentication | `flower` service in `docker-compose.yml` has no auth configured | Add `--basic_auth=admin:${FLOWER_PASSWORD}` to flower command; expose only on internal cluster network, not via Ingress |

---

### 1.7 Container Runtime (Docker — `backend/Dockerfile`, `frontend/Dockerfile`)

| Component | STRIDE Category | Threat | Existing Mitigation | Gap / Action Needed |
|---|---|---|---|---|
| `backend/Dockerfile` — root user | Elevation of Privilege | Process running as root inside container; container escape gives attacker root on host | None — no `USER` directive in either Dockerfile (TDD §22.1 gap) | Add `RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /app` + `USER appuser` to both Dockerfiles |
| Writable root filesystem | Tampering | Attacker with code execution inside container can write to any path, persist malware | None documented | Add `--read-only` flag to Docker run; mount `--tmpfs /tmp` for worker that needs temp file writes |
| Base image `python:3.11` (implied) | Information Disclosure | Unpatched OS packages in base image | `pip-audit` for Python packages only | Add Trivy container scan to CI: `trivy image toolkit-api:latest --severity HIGH,CRITICAL --exit-code 1` |
| `.env` file in repository | Information Disclosure | `.env.example` with production-like values committed; developers create `.env` with real secrets | `.env.example` only; `.env` in `.gitignore` presumably | Add TruffleHog to CI scanning entire git history; verify `.env` is in `.gitignore` (`grep "^\.env$" .gitignore`) |
| Docker Compose port exposure | Information Disclosure | `postgres:5432` and `redis:6379` exposed to host network during development | Dev-only in `docker-compose.yml` | Document that ports must not be exposed in staging/production; use K8s Services (ClusterIP) instead |

---

### 1.8 Orchestration (Kubernetes — `k8s/`)

| Component | STRIDE Category | Threat | Existing Mitigation | Gap / Action Needed |
|---|---|---|---|---|
| Pod `securityContext` | Elevation of Privilege | Pods run as root; container escape grants root on node | Not set in any `k8s/*.yaml` manifest (TDD §22.2 gap) | Add `securityContext.runAsNonRoot: true`, `runAsUser: 1000`, `readOnlyRootFilesystem: true`, `capabilities.drop: ["ALL"]`, `allowPrivilegeEscalation: false` to all pod specs |
| NetworkPolicy | Lateral Movement | Compromised API pod can reach Redis and Postgres directly, and AWS S3 via HTTPS; worker can reach Postgres and AWS S3 without restriction | Not configured (TDD §22.2 gap) | Create `NetworkPolicy` objects: API → DB:5432, API → Redis:6379; Worker → DB:5432, Worker → S3:443 (egress to AWS S3); Webhook → internet:443; deny all other ingress/egress |
| K8s Secrets | Information Disclosure | `JWT_SECRET`, `DB_PASSWORD`, `REDIS_PASSWORD`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `AIKOSH_WEBHOOK_SECRET` sourced from `.env` (TDD §21) | Not mitigated — `.env.example` approach mentioned | Use `kubectl create secret generic toolkit-secrets ...` or External Secrets Operator pointing to AWS Secrets Manager / HashiCorp Vault; mount as env vars in pod spec |
| HPA — API pods | Denial of Service | No HPA on `api` deployment (only `worker-assessment` has HPA); API flooded with requests; 3 static replicas | `worker-assessment` HPA scales 3–20 on `celery_queue_length > 10` | Add HPA for `api` deployment on CPU utilization ≥ 70%; minReplicas: 3, maxReplicas: 10 |
| K8s Dashboard / Flower Ingress | Information Disclosure | If Flower or K8s dashboard is exposed via Ingress, unauthenticated access reveals task internals | Flower has no auth (docker-compose shows no `--basic_auth`) | Restrict Flower Ingress to VPN/internal CIDR only; add `nginx.ingress.kubernetes.io/whitelist-source-range` annotation |
| PodSecurityAdmission | Elevation of Privilege | Pods can run privileged containers, mount host paths | Not configured (gap) | Label namespace: `pod-security.kubernetes.io/enforce: restricted` |
| Ingress TLS | Information Disclosure | TLS termination at Ingress; traffic from Ingress to pods is plaintext HTTP inside cluster | cert-manager handles TLS at edge (TDD §22.2) | Enable mTLS between services via service mesh (Istio/Linkerd) for zero-trust; at minimum ensure Ingress → API traffic stays on private VPC subnet |

---

### 1.9 CI/CD Pipeline (GitHub Actions)

| Component | STRIDE Category | Threat | Existing Mitigation | Gap / Action Needed |
|---|---|---|---|---|
| GitHub Actions secrets | Information Disclosure | `AIKOSH_WEBHOOK_SECRET`, `JWT_SECRET`, `DB_PASSWORD` in GitHub Actions secrets; leaked via `echo` or debug step | GitHub masks secrets in logs | Audit all workflow steps for `run: echo ${{ secrets.X }}`; add `set +x` to bash steps; never print env dumps |
| Dependency installation (`pip install -r requirements.txt`) | Supply Chain | Malicious PyPI package published with name matching a toolkit dependency (typosquatting) | `pip-audit` checks known CVEs | Pin all packages with hashes in `requirements.txt` (`pip install --require-hashes`); verify `pip-audit` runs before tests |
| Container build and push | Supply Chain | Attacker with write access to GHCR/Docker Hub pushes malicious image | Not mitigated | Sign images with `cosign` after build; add `trivy image --exit-code 1` before push; restrict push to protected branches only |
| No SAST in CI | Information Disclosure | Security bugs in Python code (e.g., `eval()`, hardcoded secrets) not caught before merge | Not mitigated (TDD only mentions `pip-audit`) | Add `bandit -r backend/ -f json` and `eslint` with `eslint-plugin-security` to every push job |
| No npm audit | Information Disclosure | Vulnerable Node.js packages deployed to frontend | Only `pip-audit` for Python (TDD §20) | Add `cd frontend && npm audit --audit-level=high` to CI dependency job |
| No secret scanning | Information Disclosure | Developer accidentally commits JWT_SECRET or S3_ACCESS_KEY to git | Not mitigated | Add TruffleHog `trufflesecurity/trufflehog@v3` action scanning every push and full history on first run |

---

### 1.10 Integration (AIKosh Webhook — `backend/app/integration/aikosh_webhook.py`)

| Component | STRIDE Category | Threat | Existing Mitigation | Gap / Action Needed |
|---|---|---|---|---|
| Webhook URL in `MetadataForm` | SSRF | `webhook_url` field accepts arbitrary URL; internal service at `http://169.254.169.254` (AWS metadata) or `http://redis:6379` reachable | Not validated beyond URL format in Pydantic | Add SSRF blocklist in `aikosh_webhook.py`: reject RFC-1918 ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16), link-local (169.254.0.0/16), and loopback (127.0.0.0/8) |
| Webhook `AIKOSH_WEBHOOK_SECRET` | Spoofing | Webhook secret in `.env`; if leaked, attacker can forge webhook payloads to AIKosh | `Authorization: Bearer <AIKOSH_WEBHOOK_SECRET>` header sent on every POST | Rotate secret regularly; AIKosh should validate signature — recommend adding HMAC-SHA256 of payload body (`X-Toolkit-Signature` header) in addition to Bearer token |
| Webhook retry (3× at 30s/120s/480s) | Denial of Service | Attacker causes webhook endpoint to return 5xx repeatedly; worker resources consumed retrying | `audit_event("aikosh_webhook_failed", {"retry_count": N})` logged | Cap total retry budget; after 3 failures, mark webhook as permanently failed and alert; do not queue exponential retries that could run for hours |
| Webhook payload — `report_url` field | Information Disclosure | `report_url` in webhook payload is a full toolkit API URL — if AIKosh re-shares this, unauthenticated parties could fetch the report | Pre-signed URLs expire after 24h | Ensure `report_url` in webhook is the API endpoint (`/api/v1/assess/{id}/report`), not the raw pre-signed S3 URL; API enforces auth before redirecting |
| Webhook response logging | Repudiation | AIKosh claims it never received assessment data; no proof of delivery in toolkit | `audit_event("aikosh_webhook_sent", {"status_code": 200})` logged | Log HTTP response body (truncated to 500 chars) and response headers in `event_detail` for non-200 responses to provide stronger proof |

---

## 2. Automated Security Testing Matrix

| # | Security Category | Specific Test | Tool / Automation | CI Trigger | How to Run (exact command) | Expected Outcome | Status |
|---|---|---|---|---|---|---|---|
| 1 | SAST — Python | Static analysis for dangerous functions (`eval`, `exec`, `shell=True`), hardcoded secrets, insecure temp file usage | Bandit | Every push to any branch | `bandit -r backend/ -f json -o reports/bandit-report.json -ll` | Zero HIGH or CRITICAL findings; report uploaded as artifact | ❌ Missing |
| 2 | SAST — TypeScript | Security linting: `no-eval`, `no-script-url`, `detect-non-literal-regexp` | ESLint + `eslint-plugin-security` | Every push | `cd frontend && npx eslint . --ext .ts,.tsx --config .eslintrc.security.json` | Zero security-category violations | ❌ Missing |
| 3 | SAST — TypeScript strict types | Type safety prevents runtime unsafe casts in API response handling | `tsc --noEmit --strict` | Every push | `cd frontend && npx tsc --noEmit --strict` | Zero type errors | ❌ Missing |
| 4 | DAST — SQL Injection | Inject SQL payloads into `dataset_name`, `target_population`, and other string metadata fields | sqlmap | Nightly against staging | `sqlmap -u "https://staging.toolkit.aikosh.gov.in/api/v1/assess" --data='{"file_key":"x","metadata":{"dataset_name":"*","dataset_type":"tabular","study_type":"cohort","target_population":"x","geographic_coverage":"district","sensitivity_class":"standard"}}' --headers="Authorization: Bearer tkt_live_test..." --batch --level=3 --risk=2` | No injectable parameters found | ❌ Missing |
| 5 | DAST — General web vulnerabilities | XSS, clickjacking, missing headers, insecure cookies | OWASP ZAP baseline scan | Nightly against staging | `docker run -t ghcr.io/zaproxy/zaproxy:stable zap-baseline.py -t https://staging.toolkit.aikosh.gov.in -r zap-report.html` | Zero MEDIUM or higher findings on security headers, XSS, cookie flags | ❌ Missing |
| 6 | SCA — Python dependencies | Known CVEs in `backend/requirements.txt` packages | pip-audit | Every push | `pip-audit -r backend/requirements.txt --format=json --output=reports/pip-audit.json` | Zero CRITICAL or HIGH CVEs; job fails and blocks merge if found | ✅ Documented |
| 7 | SCA — Node.js dependencies | Known CVEs in `frontend/package.json` | npm audit | Every push | `cd frontend && npm audit --audit-level=high --json > reports/npm-audit.json` | Zero HIGH or CRITICAL advisories | ❌ Missing |
| 8 | SCA — Container images | OS package CVEs in `toolkit-api`, `toolkit-worker`, `toolkit-frontend` images | Trivy | On every Docker build | `trivy image toolkit-api:latest --severity HIGH,CRITICAL --exit-code 1 --format json -o reports/trivy-api.json` | Zero HIGH/CRITICAL CVEs; blocks image push | ❌ Missing |
| 9 | Secret scanning — git history | Hardcoded secrets: `JWT_SECRET`, `S3_SECRET_KEY`, `AIKOSH_WEBHOOK_SECRET`, API keys | TruffleHog | Every push + full history scan on first run | `trufflehog filesystem . --json --fail` | Zero verified secrets detected; job fails on first discovery | ❌ Missing |
| 10 | API Fuzzing | Fuzz all OpenAPI endpoints with malformed inputs, type coercion, boundary values | Schemathesis | Every staging deploy | `schemathesis run https://staging.toolkit.aikosh.gov.in/openapi.json --checks all --auth "Bearer tkt_live_test..." --hypothesis-max-examples=200 --junit-xml=reports/schemathesis.xml` | Zero 5xx responses on any fuzzed endpoint; schema violations reported | ❌ Missing |
| 11 | Infrastructure — K8s hardening | CIS Kubernetes benchmark: RBAC, pod security, network policies, API server flags | kube-bench | Nightly | `kube-bench run --targets master,node --json > reports/kube-bench.json` | All FAIL items in L1 benchmark remediated before launch | ❌ Missing |
| 12 | Infrastructure — Docker hardening | CIS Docker benchmark: daemon config, image security, container runtime | docker-bench-security | Nightly | `docker run --rm --net host --pid host --userns host --cap-add audit_control -v /etc:/etc:ro -v /usr/bin/containerd:/usr/bin/containerd:ro -v /usr/bin/runc:/usr/bin/runc:ro -v /var/lib:/var/lib:ro -v /var/run/docker.sock:/var/run/docker.sock:ro docker/docker-bench-security` | Zero WARN on daemon config; non-root user findings resolved | ❌ Missing |
| 13 | BOLA / IDOR | User A cannot access User B's assessment; Admin cannot access any assessment | pytest integration | Every PR | `pytest backend/tests/test_auth_bola.py -v --tb=short` | All BOLA assertions pass (403 returned in every cross-user scenario) | ✅ Covered (`test_auth_bola.py` exists) |
| 14 | Cookie security flags | `Set-Cookie` header on login/register has `HttpOnly`, `Secure` (in production), `SameSite=Lax`, `Path=/` | pytest + httpx | Every PR | `pytest backend/tests/test_cookie_security.py -v` | All four flags present; `Secure` flag present when `ENVIRONMENT=production` | ❌ Missing (test file absent) |
| 15 | File upload security | Magic bytes mismatch rejected; file exceeding 5GB rejected; path traversal in filename rejected; ZIP bomb rejected | pytest | Every PR | `pytest backend/tests/test_file_upload_security.py -v` | 422 on magic bytes mismatch; 413 on oversized file; 422 on `../` in filename; 413 on ZIP bomb | ❌ Missing (test file absent) |
| 16 | SQL injection — unit | All ORM calls use parameterized binding; no raw SQL string interpolation | pytest | Every PR | `pytest backend/tests/test_sql_injection.py -v` | No raw SQL detected by grep fixture; ORM query execution with SQL metacharacters produces no unexpected results | ❌ Missing |
| 17 | Concurrency / race conditions | 10 simultaneous submissions from same user: no score corruption, no shared state, correct final status | pytest + asyncio | Every PR | `pytest backend/tests/test_concurrency.py -v --asyncio-mode=auto` | All 10 assessments complete independently with correct `assessment_id` isolation; no 500 responses | ❌ Missing |
| 18 | Load test | 100 concurrent users submitting assessments; API response < 2s; worker processes within 3 minutes at p95 | Locust | Nightly | `locust -f backend/tests/load/locustfile.py --headless -u 100 -r 10 --run-time 5m --csv=reports/locust` | p95 API response < 2000ms; p95 assessment completion < 180s; zero 500 errors | ❌ Missing |
| 19 | RLS / direct DB access | Application DB user (`toolkit_api`) cannot `SELECT * FROM users` via direct psql connection; cannot access other tenants' rows | psql command | Every staging deploy | `PGPASSWORD=${DB_PASSWORD} psql -h ${DB_HOST} -U toolkit_api -d toolkit_db -c "SELECT * FROM users LIMIT 1;"` (expect permission denied if RLS implemented) | `ERROR: permission denied` or empty result if RLS policy applied correctly | ❌ Missing |
| 20 | S3 direct access | Expired pre-signed URL returns 403; non-pre-signed key returns 403; report object not publicly readable | pytest + boto3 | Every PR | `pytest backend/tests/test_s3_security.py -v` | Expired URL → 403 AccessDenied; direct key access → 403; `uploads/` prefix never publicly readable | ❌ Missing |
| 21 | Rate limiting | More than 100 requests per minute from single API key → HTTP 429 with `Retry-After` header | pytest | Every PR | `pytest backend/tests/test_rate_limiting.py -v` | 101st request in 60s window returns 429; `X-RateLimit-Remaining: 0` header present | ❌ Missing |
| 22 | CSRF protection | POST to `/api/v1/assess` without correct `Origin` header from browser context returns error | pytest | Every PR | `pytest backend/tests/test_csrf.py -v` | Cross-origin POST without matching `Origin` rejected by CORS; `SameSite=Lax` prevents cross-site form submission | ❌ Missing |
| 23 | Audit log append-only | `DELETE FROM audit_logs WHERE ...` is silently ignored by PostgreSQL rule; `TRUNCATE` also blocked | pytest | Every PR | `pytest backend/tests/test_audit_append_only.py -v` | `DELETE` returns success but row count is 0; `TRUNCATE` raises `ERROR: rule blocks truncate` (after adding TRUNCATE rule) | ❌ Missing (no TRUNCATE rule yet) |
| 24 | CORS restrictive origins | `OPTIONS` preflight from disallowed origin returns no `Access-Control-Allow-Origin` header | pytest | Every PR | `pytest backend/tests/test_cors.py -v` | Requests from `https://evil.example.com` receive no CORS headers; requests from `http://localhost:3000` receive correct headers | ❌ Missing |
| 25 | Auth bypass | `GET /api/v1/assess/{uuid}` without cookie or Bearer token → 401; with tampered JWT → 401 | pytest | Every PR | `pytest backend/tests/test_auth_bypass.py -v` | No `session_token` cookie → 401 `missing_credentials`; `Authorization: Bearer invalid` → 401 `invalid_credentials` | ❌ Missing |
| 26 | Admin isolation | Admin user calls `GET /api/v1/assess/{uuid}` for any assessment → 403 | pytest | Every PR | (Covered in `backend/tests/test_auth_bola.py` — admin cannot access any assessment) | Admin JWT with role=admin returns 403 on assessment endpoint | ✅ Covered |
| 27 | Webhook retry | Mock AIKosh endpoint returning 5xx triggers exactly 3 retry attempts at correct backoff intervals | pytest + responses/respx | Integration | `pytest backend/tests/test_webhook_retry.py -v` | 3 POST attempts logged in `audit_logs`; `aikosh_webhook_failed` event after 3rd failure; Celery task marked FAILURE | ❌ Missing |
| 28 | Health endpoint data leak | `GET /api/v1/health` response does not include version details, internal IPs, or dependency error messages to unauthenticated callers | pytest | Every push | `pytest backend/tests/test_health_endpoint.py -v` | Response body contains only `{"status": "healthy"}` to unauthenticated; detailed `dependencies` object only returned to internal requests | ❌ Missing |

---

## 3. Manual Security Review Checklist

---

### 3.1 Authentication

| # | Check | What to Look For | Pass / Fail / N/A | Notes |
|---|---|---|---|---|
| 3.1.1 | Password policy enforced server-side | In `backend/app/api/v1/auth.py` — registration handler must validate password against regex `^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)(?=.*[@$!%*?&])[A-Za-z\\d@$!%*?&]{8,}$` (ref OpenAPI YAML `/api/v1/auth/register`). Must be a Pydantic field validator or explicit check, NOT only in OpenAPI schema. | ⬜ | Policy exists in OpenAPI spec; verify it is also in Pydantic `MetadataForm` or auth schema with `@validator` |
| 3.1.2 | Login rate limited 5/min per IP | `backend/app/api/v1/auth.py` login handler calls Redis rate limiter before credential check; returns 429 with `Retry-After` header if exceeded (ref TDD §20) | ⬜ | Confirm Redis key `rate_limit:login:{client_ip}` with TTL=60s and max=5 |
| 3.1.3 | JWT uses strong secret (min 256-bit) | `settings.JWT_SECRET` must be at least 32 random characters (256 bits). Check `backend/app/config.py` for any minimum length validator. | ⬜ | Add `@validator('JWT_SECRET') def must_be_strong(cls, v): assert len(v) >= 32` in `config.py` |
| 3.1.4 | JWT algorithm restricted to HS256 only | In `backend/app/api/deps.py`: `jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])` — must be explicit list, not `algorithms=jwt.algorithms.get_default_algorithms()` which would permit "none" attack | ⬜ | Grep: `grep -n "jwt.decode" backend/app/api/deps.py` — verify `algorithms=["HS256"]` |
| 3.1.5 | Logout clears cookie correctly | `POST /api/v1/auth/logout` (ref auth.py line 164-170) sets `response.delete_cookie("session_token", path="/", httponly=True, samesite="lax")` — cookie must be deleted with matching attributes | ⬜ | Verify `max_age=0` and `expires=0` used in delete; test with `test_cookie_security.py` |
| 3.1.6 | Raw API key never retrievable after creation | `api_keys.key_hash` stores only SHA-256 of raw key; `GET /api/v1/auth/keys` returns only `key_prefix` and `key_id`; raw key appears only once in `POST /api/v1/auth/keys` 201 response | ⬜ | Grep: `grep -n "raw_key" backend/app/api/v1/auth.py` — must not appear in any GET handler |
| 3.1.7 | No information leak on registration (email enumeration) | `POST /api/v1/auth/register` with existing email must return same response time and body as successful registration (or generic "if this email is new, you are registered" pattern); no "email already exists" 400 with distinct body | ⬜ | Check auth.py registration handler for early-return on duplicate email; add `asyncio.sleep(hmac.compare_digest(...))` or constant-time dummy hash |
| 3.1.8 | No "forgot password" endpoint exposes user existence | Search all registered routes in `main.py`: `grep -rn "forgot\|reset\|password" backend/app/api/` — if endpoint does not exist, document that; if it does, verify same-response policy | ⬜ | Feature not in PRD §19 or OpenAPI §7 — confirm endpoint does not exist |

---

### 3.2 Session Management

| # | Check | What to Look For | Pass / Fail / N/A | Notes |
|---|---|---|---|---|
| 3.2.1 | `session_token` cookie is `HttpOnly` | `backend/app/api/v1/auth.py:64` — `response.set_cookie(..., httponly=True, ...)` | ⬜ | Confirmed in TDD §17.1; verify in test: `assert "HttpOnly" in response.headers["set-cookie"]` |
| 3.2.2 | `session_token` cookie is `Secure` in production | `auth.py:69` currently `secure=False` — **this is a P0 gap**. Must be `secure=settings.ENVIRONMENT == "production"` | ❌ GAP | Change to `secure=(settings.ENVIRONMENT == "production")` before production deploy |
| 3.2.3 | `session_token` cookie has `SameSite=Lax` | `auth.py:68` — `samesite="lax"` | ⬜ | Verify in cookie header; "Lax" prevents cross-site POST but not GET-based CSRF (acceptable for this API) |
| 3.2.4 | `session_token` cookie has explicit `Path=/` | `auth.py:67` — `path="/"` must be set to prevent cookie scoping to only `/api/` path | ⬜ | Verify `Path=/` in `Set-Cookie` header |
| 3.2.5 | No session data in `localStorage` or `sessionStorage` | `frontend/stores/auth.ts` (Zustand) and `frontend/lib/api/client.ts` — Zustand store must use in-memory state only (`persist` middleware with `sessionStorage` would be insecure) | ⬜ | `grep -rn "localStorage\|sessionStorage" frontend/` — must return zero results |
| 3.2.6 | No token in URL query parameters | Search all `frontend/lib/api/client.ts` fetch calls — no `?token=` or `?session=` patterns | ⬜ | `grep -rn "token=" frontend/lib/` — must return zero URL-embedded token usage |
| 3.2.7 | Session duration acceptable for risk level | `JWT_EXPIRY_MINUTES=43200` (30 days) — for a system handling sensitive health research datasets, 30 days may be too long; consider 24h with refresh | ⬜ | Decision: document rationale in AGENTS.md; if 30 days chosen, add explicit user-visible "Active session" warning in UI |
| 3.2.8 | No refresh token rotation mechanism | No refresh token exists in architecture (ref PRD §19, OpenAPI §3.1) — 30-day JWT cannot be revoked before expiry without a token blocklist | ⬜ | Gap: either add Redis-based JWT blocklist for logout (check `auth.py logout` handler adds token to blocklist) or reduce JWT TTL to 24h |

---

### 3.3 Access Control (BOLA / IDOR)

| # | Check | What to Look For | Pass / Fail / N/A | Notes |
|---|---|---|---|---|
| 3.3.1 | User A cannot access User B's assessment | DB query in `api/v1/assess.py` `GET /{assessment_id}` handler: `WHERE assessment_id = :id AND user_id = :current_user_id` — NOT just `WHERE assessment_id = :id` | ⬜ | Covered by `test_auth_bola.py`; verify the SQL query itself (not just HTTP response) adds user_id filter |
| 3.3.2 | User A cannot download User B's report | `GET /api/v1/assess/{assessment_id}/report` checks same user ownership before generating pre-signed URL | ⬜ | Covered in `test_auth_bola.py`; verify pre-signed URL generation is gated by same ownership check as status endpoint |
| 3.3.3 | Admin cannot view any assessment data or reports | Admin JWT (role=admin) calling `GET /api/v1/assess/{any_id}` returns 403 `insufficient_permissions` | ⬜ | Covered in `test_auth_bola.py`; confirm `deps.py` enforces admin exclusion from assessment routes explicitly |
| 3.3.4 | Reviewer sees audit logs but NOT assessment results | `GET /api/v1/assess/{id}/audit` returns 200 for reviewer; `GET /api/v1/assess/{id}` returns 403 for reviewer (reviewer ≠ submitter) | ⬜ | Not tested — add case to `test_auth_bola.py` or new `test_reviewer_access.py` |
| 3.3.5 | Non-admin user cannot access `/api/v1/admin/*` | `GET /api/v1/admin/users` with user or reviewer JWT → 403 | ⬜ | Add to `test_auth_bypass.py`: assert user role → 403, reviewer role → 403, admin role → 200 |
| 3.3.6 | API key from User A cannot access User B's data | Bearer token `tkt_live_UserA...` → `GET /api/v1/assess/{UserB_assessment_id}` → 403 | ⬜ | `test_auth_bola.py` uses `generate_test_jwt()` — add parallel test with Bearer API key mechanism |
| 3.3.7 | Mass assignment prevention on metadata form | `POST /api/v1/assess` `metadata` body — Pydantic `MetadataForm` schema in `backend/app/schemas/metadata_form.py` must use `model_config = ConfigDict(extra='forbid')` to reject undeclared fields | ⬜ | `grep -n "extra" backend/app/schemas/metadata_form.py` — must show `extra='forbid'` |

---

### 3.4 Input Validation

| # | Check | What to Look For | Pass / Fail / N/A | Notes |
|---|---|---|---|---|
| 3.4.1 | SQL injection — all queries parameterized | All `backend/app/models/*.py` and query files use SQLAlchemy ORM or `select().where(Model.col == :param)` — never `f"WHERE col = '{user_input}'"` | ⬜ | `grep -rn "f\"" backend/app/models/ backend/app/api/` for f-string SQL; `grep -rn "text(" backend/app/` for raw SQL |
| 3.4.2 | No `eval()` or `exec()` on user input | Profiler, domain scorers, and report generator must not call `eval()` on any data from uploaded files or metadata | ⬜ | `grep -rn "eval(\|exec(" backend/app/engine/ backend/app/worker/` — must return zero results |
| 3.4.3 | File upload extension whitelist enforced | `backend/app/engine/ingestion/validator.py` — allowed extensions: `.csv`, `.xlsx`, `.json`, `.parquet`, `.fhir.json`, `.zip`, `.tsv`; all others return 422 `unsupported_format` | ⬜ | Covered in `test_file_upload_security.py`; verify whitelist is a constant, not just documented |
| 3.4.4 | File size limit enforced at 5GB | `settings.MAX_FILE_SIZE_BYTES = 5_368_709_120` in `config.py`; enforced before writing to S3 (pre-signed URL flow) or in multipart handler (current flow) | ⬜ | Current multipart path: verify FastAPI/Starlette `max_size` parameter in `UploadFile` handling |
| 3.4.5 | Magic bytes / MIME type verified | `backend/app/engine/ingestion/validator.py` checks file magic bytes (e.g., CSV starts with printable ASCII, XLSX starts with `PK\x03\x04`, Parquet starts with `PAR1`) — not just extension | ⬜ | No automated test exists — `test_file_upload_security.py` must include magic bytes mismatch (e.g., `.csv` file with ELF header) |
| 3.4.6 | ZIP bomb protection | ZIP extraction in `engine/ingestion/parser.py` enforces max extract size = 10× compressed size or 500MB absolute; does not recurse more than 1 level | ⬜ | `grep -n "zipfile\|ZipFile" backend/app/engine/ingestion/parser.py` — verify extract size check exists |
| 3.4.7 | Path traversal prevention | `secure_filename()` applied to uploaded filenames (ref TDD §20); S3 key constructed as `uploads/{assessment_id}/dataset.{safe_ext}` — never includes user-supplied filename | ⬜ | Verify S3 key generation in `storage/s3_client.py` does not use raw `filename` from `UploadFile.filename` |
| 3.4.8 | XSS — Jinja2 template escaping | `backend/app/reports/generator.py` — `Environment(autoescape=True)` or `Environment(loader=..., autoescape=select_autoescape(['html']))` | ⬜ | `grep -n "autoescape" backend/app/reports/generator.py` — must be True; `grep -n "| safe" backend/app/reports/templates/quality_report.html` — must be zero |
| 3.4.9 | XSS — Next.js frontend | `frontend/components/domain-score-table.tsx`, `gap-panel.tsx`, `score-history.tsx` — no `dangerouslySetInnerHTML` usage | ⬜ | `grep -rn "dangerouslySetInnerHTML" frontend/` — must return zero results |
| 3.4.10 | SSRF — webhook URL validation | `backend/app/integration/aikosh_webhook.py` — before HTTP client call, resolve `webhook_url` hostname and reject if IP is RFC-1918, loopback, or link-local | ⬜ | Not documented in TDD §14; add validation using `ipaddress.ip_address()` after DNS resolution |
| 3.4.11 | Open redirect — report URL | `GET /api/v1/assess/{id}/report` 302 redirect — `Location` header must always point to `*.amazonaws.com` or configured AWS S3 domain, never to user-supplied URL | ⬜ | Pre-signed URL generated by `s3_client.py` resolves to standard AWS S3 domains — user cannot influence the domain |

---

### 3.5 Cryptography

| # | Check | What to Look For | Pass / Fail / N/A | Notes |
|---|---|---|---|---|
| 3.5.1 | bcrypt cost factor ≥ 12 | `backend/app/api/v1/auth.py` uses `passlib[bcrypt]`; `CryptContext(schemes=["bcrypt"], deprecated="auto")` defaults to cost 12 — verify not overridden to lower value | ⬜ | `grep -n "bcrypt\|CryptContext" backend/app/api/v1/auth.py` — check `rounds` parameter |
| 3.5.2 | JWT secret minimum entropy | `settings.JWT_SECRET` must be minimum 32 randomly-generated characters; must not be a dictionary word or predictable pattern | ⬜ | Add Pydantic validator: `assert len(v) >= 32 and not v.isalpha()` |
| 3.5.3 | API key entropy | Key generated as `tkt_live_{32 random alphanumeric}` — 32 chars from 62-character alphabet = ~190 bits entropy; sufficient | ⬜ | `grep -n "secrets\|urandom\|token_urlsafe" backend/app/api/v1/auth.py` — must use `secrets.token_urlsafe(24)` or similar |
| 3.5.4 | TLS 1.3 at ingress | K8s Ingress annotation: `nginx.ingress.kubernetes.io/ssl-protocols: "TLSv1.3"` in `k8s/ingress.yaml` | ⬜ | Verify ingress config; also add `nginx.ingress.kubernetes.io/ssl-ciphers: "TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256"` |
| 3.5.5 | HSTS header not currently set | Gap — no `Strict-Transport-Security` header in any middleware or Nginx config | ❌ GAP | Add to FastAPI middleware: `response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"` (only when HTTPS) |
| 3.5.6 | S3 server-side encryption | S3 bucket has `ServerSideEncryptionConfiguration` with `SSEAlgorithm: AES256` | ⬜ | Verify with: `aws s3api get-bucket-encryption --bucket aikosh-datasets` |

---

### 3.6 Infrastructure & Configuration

| # | Check | What to Look For | Pass / Fail / N/A | Notes |
|---|---|---|---|---|
| 3.6.1 | No secrets in `docker-compose.yml` | `docker-compose.yml` references `env_file: .env` — all secret values must be in `.env` (gitignored), not hardcoded in `docker-compose.yml` | ⬜ | `grep -n "PASSWORD\|SECRET\|KEY" docker-compose.yml` — must return only variable references like `${DB_PASSWORD}`, not literal values |
| 3.6.2 | No secrets in K8s manifests | `k8s/api-deployment.yaml`, `worker-deployment.yaml` — all env vars with secrets must reference `secretKeyRef`, never `value: hardcoded` | ⬜ | `grep -rn "value:" k8s/` — verify no sensitive values hardcoded |
| 3.6.3 | Docker containers non-root | `backend/Dockerfile` and `frontend/Dockerfile` must include `USER 1000:1000` directive after dependencies installed | ❌ GAP | Add to both Dockerfiles: `RUN addgroup --gid 1000 appgroup && adduser --uid 1000 --gid 1000 --disabled-password appuser && chown -R appuser:appgroup /app` then `USER appuser` |
| 3.6.4 | Read-only root filesystem | Celery worker needs writable `/tmp` for temp dataset processing; API and frontend can use `--read-only --tmpfs /tmp` | ⬜ | Add to worker K8s pod spec: `volumeMounts: [{mountPath: /tmp, name: tmp-volume}]` + `volumes: [{name: tmp-volume, emptyDir: {}}]`; set `readOnlyRootFilesystem: true` |
| 3.6.5 | K8s Pod Security Standards enforced | Namespace label `pod-security.kubernetes.io/enforce: restricted` ensures pods cannot run privileged, host network, or as root | ❌ GAP | `kubectl label namespace toolkit-prod pod-security.kubernetes.io/enforce=restricted` |
| 3.6.6 | K8s NetworkPolicy isolates services | Each service (api, worker, db, redis) has explicit `NetworkPolicy` allowing only necessary traffic | ❌ GAP | Create `k8s/network-policies.yaml` — see Section 7 hardening guide for full spec |
| 3.6.7 | Redis requires password | `docker-compose.yml` Redis service: `command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}` — currently no password documented | ❌ GAP | Add `requirepass` and update `settings.REDIS_URL` to `redis://:${REDIS_PASSWORD}@redis:6379/0` |
| 3.6.8 | PostgreSQL uses `scram-sha-256` auth | `pg_hba.conf` in postgres container must not have `trust` method for any host; use `scram-sha-256` | ⬜ | Docker postgres image defaults to `md5`; override with `POSTGRES_PASSWORD` env var which sets `md5`; explicitly set `POSTGRES_HOST_AUTH_METHOD=scram-sha-256` |
| 3.6.9 | AWS S3 bucket not publicly accessible | S3 bucket Public Access Block configured to block all public ACLs/policies; all access via pre-signed URLs only | ⬜ | Verify with: `aws s3api get-public-access-block --bucket aikosh-datasets` |
| 3.6.10 | CORS origins no wildcard | `settings.CORS_ORIGINS` never includes `"*"` in any environment; AGENTS.md §9 "What NOT To Do" explicitly warns against this | ⬜ | `grep -rn "CORS_ORIGINS" backend/app/config.py` — must be explicit list like `["http://localhost:3000", "https://toolkit.aikosh.gov.in"]` |

---

### 3.7 CI/CD Security

| # | Check | What to Look For | Pass / Fail / N/A | Notes |
|---|---|---|---|---|
| 3.7.1 | No secrets logged in CI | All `.github/workflows/*.yml` steps — no `echo ${{ secrets.* }}` or `env` dump commands | ⬜ | `grep -rn "echo.*secrets\|env.*secrets" .github/workflows/` — must be zero |
| 3.7.2 | `npm audit` runs on every PR | `.github/workflows/` contains `cd frontend && npm audit --audit-level=high` step | ❌ GAP | Only `pip-audit` documented in TDD §20; add `npm audit` to CI (see Section 4) |
| 3.7.3 | Bandit SAST on every push | `.github/workflows/` contains `bandit -r backend/` step | ❌ GAP | Add `sast-python` job (see Section 4) |
| 3.7.4 | Container scanning before deploy | Trivy scans `toolkit-api:latest` and `toolkit-worker:latest` images before any push to registry | ❌ GAP | Add `docker-scan` job to `security-scan.yml` (see Section 4) |
| 3.7.5 | Docs UI disabled in production | `backend/app/main.py` FastAPI instantiation: `app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)` when `settings.ENVIRONMENT == "production"` | ⬜ | `grep -n "docs_url\|redoc_url" backend/app/main.py` — verify conditional on environment |

---

### 3.8 Monitoring & Incident Response

| # | Check | What to Look For | Pass / Fail / N/A | Notes |
|---|---|---|---|---|
| 3.8.1 | Security events logged to `audit_logs` | Failed login attempts, rate limit hits, BOLA attempts (403 on cross-user access), auth failures — all write `audit_log` event with `severity=WARNING` or `severity=ERROR` | ⬜ | `grep -n "audit_event" backend/app/api/v1/auth.py` — verify failed login writes `login_failed` event |
| 3.8.2 | Alerting on >5% assessment failure rate | Prometheus alert rule in Grafana: `rate(assessment_failures_total[5m]) / rate(assessments_total[5m]) > 0.05` → PagerDuty/Slack alert | ⬜ | TDD §24 documents key metrics; verify Grafana alert rule exists in `k8s/` monitoring config |
| 3.8.3 | Webhook delivery failure monitored | Flower + Grafana show `webhook` queue depth; alert when `aikosh_webhook_failed` event count > 10 in 1h | ⬜ | TDD §24 mentions Flower; verify `aikosh_webhook_failed` counter is a Prometheus metric |
| 3.8.4 | Incident response plan documented | A documented runbook exists: "What to do if JWT_SECRET is leaked", "What to do if S3 bucket is misconfigured", "What to do if DB credentials are compromised" | ❌ GAP | No incident response plan in any document; create `docs/INCIDENT_RESPONSE.md` with runbook templates |
| 3.8.5 | Security disclosure policy | `SECURITY.md` at repo root with responsible disclosure contact, GPG key, and SLA for response | ❌ GAP | Create `SECURITY.md`; nominate a security contact within AIKosh/IndiaAI team |

---

## 4. CI/CD Pipeline Integration

```yaml
# .github/workflows/security-scan.yml
name: Security Scan

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    # Nightly scans at 02:00 UTC
    - cron: '0 2 * * *'

env:
  PYTHON_VERSION: '3.11'
  NODE_VERSION: '20'

jobs:

  # ── Job 1: Python SAST ──────────────────────────────────────────────────────
  sast-python:
    name: SAST — Bandit (Python)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install Bandit
        run: pip install bandit[toml]==1.7.9

      - name: Run Bandit
        run: |
          bandit -r backend/ \
            -f json \
            -o reports/bandit-report.json \
            -ll \
            --exclude backend/tests/
        continue-on-error: false  # Fail CI on HIGH/CRITICAL findings

      - name: Upload Bandit report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: bandit-report
          path: reports/bandit-report.json


  # ── Job 2: TypeScript SAST ──────────────────────────────────────────────────
  sast-typescript:
    name: SAST — ESLint + tsc (TypeScript)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install frontend dependencies
        run: cd frontend && npm ci

      - name: ESLint security plugin
        run: |
          cd frontend
          npx eslint . \
            --ext .ts,.tsx \
            --plugin security \
            --rule 'security/detect-eval-with-expression: error' \
            --rule 'security/detect-non-literal-fs-filename: warn' \
            --rule 'security/detect-possible-timing-attacks: warn' \
            --max-warnings=0

      - name: TypeScript strict type check
        run: cd frontend && npx tsc --noEmit --strict


  # ── Job 3: Dependency Scanning ──────────────────────────────────────────────
  dependency-scan:
    name: SCA — pip-audit + npm audit
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: pip-audit (Python dependencies)
        run: |
          pip install pip-audit==2.7.3
          pip-audit \
            -r backend/requirements.txt \
            --format=json \
            --output=reports/pip-audit.json
        # Fails on any CVE with CVSS >= 7.0

      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: npm audit (Node.js dependencies)
        run: |
          cd frontend && npm ci
          npm audit \
            --audit-level=high \
            --json > ../reports/npm-audit.json 2>&1 || true
          # Parse exit code manually to control threshold
          npm audit --audit-level=high

      - name: Upload dependency reports
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: dependency-audit-reports
          path: reports/


  # ── Job 4: Secret Scanning ──────────────────────────────────────────────────
  secret-scan:
    name: Secret Scanning — TruffleHog
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for first-run scan

      - name: TruffleHog — scan commits since last push
        uses: trufflesecurity/trufflehog@v3
        with:
          path: ./
          base: ${{ github.event.repository.default_branch }}
          head: HEAD
          extra_args: --only-verified --json

      - name: TruffleHog — filesystem scan (nightly only)
        if: github.event_name == 'schedule'
        uses: trufflesecurity/trufflehog@v3
        with:
          path: ./
          extra_args: --only-verified --json


  # ── Job 5: Container Image Scanning ─────────────────────────────────────────
  docker-scan:
    name: SCA — Trivy Container Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build API image
        run: docker build -t toolkit-api:${{ github.sha }} ./backend

      - name: Build worker image (same Dockerfile, different CMD)
        run: docker build -t toolkit-worker:${{ github.sha }} ./backend

      - name: Build frontend image
        run: docker build -t toolkit-frontend:${{ github.sha }} ./frontend

      - name: Trivy scan — API image
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: toolkit-api:${{ github.sha }}
          format: 'json'
          output: 'reports/trivy-api.json'
          severity: 'HIGH,CRITICAL'
          exit-code: '1'

      - name: Trivy scan — Worker image
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: toolkit-worker:${{ github.sha }}
          format: 'json'
          output: 'reports/trivy-worker.json'
          severity: 'HIGH,CRITICAL'
          exit-code: '1'

      - name: Trivy scan — Frontend image
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: toolkit-frontend:${{ github.sha }}
          format: 'json'
          output: 'reports/trivy-frontend.json'
          severity: 'HIGH,CRITICAL'
          exit-code: '1'

      - name: Upload Trivy reports
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: trivy-reports
          path: reports/trivy-*.json


  # ── Job 6: Security Integration Tests ───────────────────────────────────────
  security-integration-tests:
    name: Security Integration Tests (pytest)
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: toolkit_test
          POSTGRES_USER: toolkit_test
          POSTGRES_PASSWORD: test_password_ci_only
        ports: ['5432:5432']
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7.2-alpine
        ports: ['6379:6379']
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install backend dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install pytest pytest-asyncio httpx pyjwt respx faker

      - name: Run Alembic migrations on test DB
        run: |
          cd backend
          alembic upgrade head
        env:
          DATABASE_URL: postgresql+asyncpg://toolkit_test:test_password_ci_only@localhost:5432/toolkit_test

      - name: Run all security test suites
        run: |
          pytest \
            backend/tests/test_auth_bola.py \
            backend/tests/test_cookie_security.py \
            backend/tests/test_file_upload_security.py \
            backend/tests/test_sql_injection.py \
            backend/tests/test_concurrency.py \
            backend/tests/test_auth_bypass.py \
            backend/tests/test_cors.py \
            backend/tests/test_rate_limiting.py \
            backend/tests/test_csrf.py \
            backend/tests/test_audit_append_only.py \
            backend/tests/test_s3_security.py \
            backend/tests/test_webhook_retry.py \
            backend/tests/test_health_endpoint.py \
            -v \
            --tb=short \
            --junit-xml=reports/security-tests.xml
        env:
          DATABASE_URL: postgresql+asyncpg://toolkit_test:test_password_ci_only@localhost:5432/toolkit_test
          REDIS_URL: redis://localhost:6379/0
          JWT_SECRET: ci-test-secret-32-characters-min
          JWT_ALGORITHM: HS256
          ENVIRONMENT: test
          CORS_ORIGINS: '["http://localhost:3000"]'
          S3_ENDPOINT_URL: http://localhost:9000
          S3_BUCKET_NAME: test-bucket
          S3_ACCESS_KEY: testkey
          S3_SECRET_KEY: testsecret
          MAX_FILE_SIZE_BYTES: 5368709120
          TOOLKIT_VERSION: 1.0.0

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: security-test-results
          path: reports/security-tests.xml


  # ── Job 7: API Fuzzing (staging deploy only) ────────────────────────────────
  api-fuzzing:
    name: API Fuzzing — Schemathesis
    runs-on: ubuntu-latest
    if: github.event_name == 'schedule' || github.ref == 'refs/heads/main'
    environment: staging
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install Schemathesis
        run: pip install schemathesis==3.34.x

      - name: Run Schemathesis fuzzer against staging
        run: |
          schemathesis run \
            https://staging.toolkit.aikosh.gov.in/openapi.json \
            --checks all \
            --auth "Bearer ${{ secrets.STAGING_API_KEY }}" \
            --hypothesis-max-examples=200 \
            --validate-schema=true \
            --junit-xml=reports/schemathesis.xml \
            --exclude-path "/api/v1/health" \
            --exit-first
        continue-on-error: false

      - name: Upload Schemathesis report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: schemathesis-report
          path: reports/schemathesis.xml


  # ── Job 8: Infrastructure Hardening (nightly) ───────────────────────────────
  infra-hardening:
    name: Infrastructure Hardening — kube-bench + docker-bench
    runs-on: ubuntu-latest
    if: github.event_name == 'schedule'
    environment: staging
    steps:
      - uses: actions/checkout@v4

      - name: Run kube-bench against staging cluster
        run: |
          kubectl run kube-bench \
            --image=aquasec/kube-bench:latest \
            --restart=Never \
            --overrides='{"spec": {"hostPID": true, "hostIPC": true, "hostNetwork": true, "containers": [{"name": "kube-bench", "image": "aquasec/kube-bench:latest", "command": ["kube-bench", "run", "--targets", "master,node", "--json"], "volumeMounts": [{"name": "var-lib-kubelet", "mountPath": "/var/lib/kubelet"}, {"name": "etc-systemd", "mountPath": "/etc/systemd"}, {"name": "etc-kubernetes", "mountPath": "/etc/kubernetes"}]}]}}' \
            -- kube-bench run --targets master,node --json > reports/kube-bench.json
        env:
          KUBECONFIG: ${{ secrets.STAGING_KUBECONFIG }}

      - name: Run docker-bench-security
        run: |
          docker run --rm \
            --net host \
            --pid host \
            --userns host \
            --cap-add audit_control \
            -v /etc:/etc:ro \
            -v /usr/bin/containerd:/usr/bin/containerd:ro \
            -v /usr/bin/runc:/usr/bin/runc:ro \
            -v /var/lib:/var/lib:ro \
            -v /var/run/docker.sock:/var/run/docker.sock:ro \
            docker/docker-bench-security \
            --json > reports/docker-bench.json

      - name: Upload infra reports
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: infra-hardening-reports
          path: reports/


  # ── Job 9: DAST (nightly against staging) ───────────────────────────────────
  dast-owasp-zap:
    name: DAST — OWASP ZAP Baseline
    runs-on: ubuntu-latest
    if: github.event_name == 'schedule'
    environment: staging
    steps:
      - uses: actions/checkout@v4

      - name: Run ZAP Baseline Scan
        uses: zaproxy/action-baseline@v0.12.0
        with:
          target: 'https://staging.toolkit.aikosh.gov.in'
          rules_file_name: '.zap/rules.tsv'
          cmd_options: '-a -j -r zap-report.html'

      - name: Upload ZAP report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: zap-report
          path: zap-report.html


  # ── Job 10: Load Test (nightly) ─────────────────────────────────────────────
  load-test:
    name: Load Test — Locust
    runs-on: ubuntu-latest
    if: github.event_name == 'schedule'
    environment: staging
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install Locust
        run: pip install locust==2.29.x

      - name: Run load test — 100 users, 5 minutes
        run: |
          locust \
            -f backend/tests/load/locustfile.py \
            --headless \
            -u 100 \
            -r 10 \
            --run-time 5m \
            --host https://staging.toolkit.aikosh.gov.in \
            --csv=reports/locust \
            --exit-code-on-error 1
        env:
          LOAD_TEST_API_KEY: ${{ secrets.STAGING_API_KEY }}

      - name: Upload Locust report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: load-test-results
          path: reports/locust*.csv
```

---

## 5. Remediation Priority Matrix

| Priority | Issue | Effort | Category | Action Required | Owner |
|---|---|---|---|---|---|
| **P0** | `secure=False` hardcoded in `backend/app/api/v1/auth.py:69` — session cookie transmitted over HTTP | Small | Auth / Session | Replace with `secure=(settings.ENVIRONMENT == "production")` in `response.set_cookie()` call | Person 1 (Backend) |
| **P0** | No `Strict-Transport-Security` (HSTS) header | Small | Transport Security | Add `SecurityHeadersMiddleware` in `backend/app/main.py` setting `Strict-Transport-Security: max-age=31536000; includeSubDomains`; also add to `next.config.ts` headers | Person 1 (Backend) + Person 3 (Frontend) |
| **P0** | No `Content-Security-Policy` header on API or frontend | Small | XSS Prevention | Add CSP in FastAPI middleware (`default-src 'self'`) and in `next.config.ts` async `headers()` function | Person 1 + Person 3 |
| **P0** | No `X-Content-Type-Options: nosniff` header | Small | MIME Sniffing | Add to `SecurityHeadersMiddleware` in `main.py`; add to `next.config.ts` headers | Person 1 + Person 3 |
| **P0** | Redis has no `requirepass` — any pod in cluster can connect and read/write Celery task queue | Small | Message Broker | Add `--requirepass ${REDIS_PASSWORD}` to Redis command in `docker-compose.yml` and K8s Redis deployment; update `settings.REDIS_URL` | Person 2 (Infrastructure) |
| **P0** | Docker containers run as root — no `USER` directive in `backend/Dockerfile` or `frontend/Dockerfile` | Small | Container Security | Add non-root user creation and `USER 1000:1000` to both Dockerfiles before first production build | Person 2 |
| **P0** | No K8s `NetworkPolicy` — all pods can communicate freely; compromised API can reach DB directly | Medium | Network Security | Create `k8s/network-policies.yaml` with explicit allow rules (API→DB:5432, API→Redis:6379, Worker→DB:5432, Worker→S3:443, Webhook→443); deny all other cross-service traffic | Person 2 |
| **P0** | No SAST (Bandit or ESLint with security plugin) in CI | Small | CI/CD | Add `sast-python` and `sast-typescript` jobs to `.github/workflows/security-scan.yml` (see Section 4) | Person 2 (DevOps) |
| **P0** | No `npm audit` in CI — frontend Node.js dependencies unscanned | Small | Supply Chain | Add `cd frontend && npm audit --audit-level=high` to `dependency-scan` job in CI | Person 2 |
| **P0** | No container image scanning in CI — CVEs in base images undetected before deploy | Small | Supply Chain | Add `docker-scan` job with `trivy image toolkit-api:latest --severity HIGH,CRITICAL --exit-code 1` (see Section 4) | Person 2 |
| **P0** | No SSRF validation on `webhook_url` field in `MetadataForm` — attacker can probe internal services | Medium | Input Validation | Add IP blocklist check in `backend/app/integration/aikosh_webhook.py` before `httpx.post()` call; reject RFC-1918, loopback, link-local | Person 1 |
| **P0** | JWT "none" algorithm attack possible if `algorithms` param is not explicit list in `deps.py` | Small | Cryptography | Verify `jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])` in `backend/app/api/deps.py`; add test in `test_auth_bypass.py` | Person 1 |
| **P1** | No HPA for `api` deployment — only `worker-assessment` auto-scales; API can be DoS'd with 3 static replicas | Medium | Availability | Add HPA for `api` deployment in `k8s/api-deployment.yaml`: min 3, max 10, scale on CPU ≥ 70% | Person 2 |
| **P1** | No read-only root filesystem on containers | Small | Container Security | Add `readOnlyRootFilesystem: true` in K8s pod `securityContext`; mount `emptyDir` at `/tmp` for worker | Person 2 |
| **P1** | Password policy only in OpenAPI spec — not verified to exist as server-side Pydantic validator in `auth.py` | Small | Auth | Add Pydantic `@field_validator('password')` in `backend/app/schemas/assessment.py` auth schema enforcing the regex `^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)(?=.*[@$!%*?&])[A-Za-z\\d@$!%*?&]{8,}$` | Person 1 |
| **P1** | No load testing suite — processing time SLA (< 3 min for 1GB) unverified | Medium | Performance | Create `backend/tests/load/locustfile.py` simulating 100 concurrent users submitting datasets of varying sizes; run nightly via `locust --headless -u 100` | Person 3 (Testing) |
| **P1** | No concurrency tests for race conditions in assessment pipeline — domain scorer state could be shared | Medium | Correctness / Security | Create `backend/tests/test_concurrency.py` submitting 10 simultaneous assessments from same user; assert each receives correct isolated `assessment_id` and final status | Person 3 |
| **P1** | No automated magic bytes test for file upload — MIME mismatch check is documented but untested | Small | Input Validation | Create `backend/tests/test_file_upload_security.py` with ELF binary renamed to `.csv`; assert 422 response | Person 3 |
| **P1** | No session token rotation / refresh mechanism — 30-day JWT cannot be revoked without token blocklist | Large | Session Management | Option A: Add Redis-based JWT blocklist (`logout` adds token hash); Option B: Reduce TTL to 24h and implement refresh token endpoint; document chosen approach in AGENTS.md | Person 1 |
| **P1** | Single DB user for all services — API and worker share same PostgreSQL credentials | Medium | Least Privilege | Create `toolkit_api` (read/write on API tables) and `toolkit_worker` (write on result tables) roles; update `config.py` to support two `DATABASE_URL` variants | Person 1 + Person 2 |
| **P2** | No TruffleHog secret scanning in CI — developer could commit `JWT_SECRET` or S3 credentials | Small | Supply Chain | Add `secret-scan` job with `trufflesecurity/trufflehog@v3` to CI (see Section 4 workflow) | Person 2 |
| **P2** | No API fuzzing (Schemathesis) — edge cases in OpenAPI schema validation untested | Medium | Testing | Add `api-fuzzing` job to nightly CI targeting staging (see Section 4); requires staging API key in GitHub Secrets | Person 3 |
| **P2** | No DAST scans scheduled — dynamic vulnerability testing absent | Medium | Testing | Add OWASP ZAP baseline scan to nightly CI against staging (see Section 4 `dast-owasp-zap` job) | Person 2 |
| **P2** | No backup / DR plan for PostgreSQL — assessment results and audit logs at risk if DB volume lost | Large | Availability | Implement automated PostgreSQL backups to S3 (pg_dump + PITR via WAL archiving); document RTO/RPO targets; test restore procedure quarterly | Person 2 |
| **P2** | No incident response plan documented | Medium | Governance | Create `docs/INCIDENT_RESPONSE.md` with runbooks for: JWT secret leak, S3 misconfiguration, DB compromise, webhook secret exposure | Person 2 |
| **P2** | Grafana alerting rules for security events not defined | Medium | Monitoring | Define Prometheus alert rules for: login failure rate > 10/min, assessment failure rate > 5%, webhook failure rate > 10%, rate limit hit rate > 50/min | Person 2 |
| **P2** | No separate PostgreSQL role per service (all services share one `DATABASE_URL`) | Medium | Least Privilege | Create `toolkit_api`, `toolkit_worker`, `toolkit_readonly` roles with scoped permissions (see Section 7 PostgreSQL hardening) | Person 1 |
| **P2** | Flower (Celery monitor) exposed without authentication on port 5555 | Small | Information Disclosure | Add `--basic_auth=admin:${FLOWER_PASSWORD}` to Flower start command; restrict Ingress to internal CIDR | Person 2 |
| **P3** | Rate limiting not applied to assessment submission endpoints (only login/register) | Medium | DoS Prevention | Add rate limit middleware to `POST /api/v1/assess` (separate bucket from auth endpoints); existing 10 concurrent assessment limit provides partial protection | Person 1 |
| **P3** | `X-Frame-Options` header not set | Small | Clickjacking | Add `X-Frame-Options: DENY` to `SecurityHeadersMiddleware` in `main.py` and to `next.config.ts` headers | Person 1 + Person 3 |
| **P3** | No explicit `Domain` attribute on `session_token` cookie | Small | Session | Add `domain=settings.COOKIE_DOMAIN` to `response.set_cookie()` call; configure `COOKIE_DOMAIN` in `config.py` | Person 1 |
| **P3** | No K8s `PodSecurityAdmission` label on namespace | Small | Container Security | `kubectl label namespace toolkit-prod pod-security.kubernetes.io/enforce=restricted pod-security.kubernetes.io/warn=restricted` | Person 2 |
| **P3** | Health endpoint leaks dependency status and version string to unauthenticated callers | Small | Information Disclosure | Return `{"status": "healthy"}` only to external callers; return full `dependencies` object only when `X-Internal-Request: true` header present from ingress/load balancer | Person 1 |

---

## 6. Alignment with OWASP Standards

| Checklist Item | OWASP ASVS Level | OWASP API Security Top 10 (2023) Ref | OWASP Top 10 (2021) Ref | Status |
|---|---|---|---|---|
| 3.1.1 — Password policy server-side | L1 — V2.1.1 | API8:2023 Security Misconfiguration | A07:2021 Identification and Authentication Failures | ⬜ |
| 3.1.2 — Login rate limited 5/min per IP | L1 — V2.2.1 | API4:2023 Unrestricted Resource Consumption | A07:2021 Identification and Authentication Failures | ⬜ |
| 3.1.3 — JWT strong secret (256-bit) | L2 — V2.6.1 | API2:2023 Broken Authentication | A07:2021 Identification and Authentication Failures | ⬜ |
| 3.1.4 — JWT algorithm restricted (no "none") | L1 — V2.6.3 | API2:2023 Broken Authentication | A02:2021 Cryptographic Failures | ⬜ |
| 3.1.5 — Logout clears cookie | L1 — V3.3.1 | API2:2023 Broken Authentication | A07:2021 Identification and Authentication Failures | ⬜ |
| 3.1.6 — Raw API key never retrievable | L2 — V2.8.2 | API2:2023 Broken Authentication | A02:2021 Cryptographic Failures | ⬜ |
| 3.1.7 — No email enumeration on register | L2 — V2.2.2 | API2:2023 Broken Authentication | A07:2021 Identification and Authentication Failures | ⬜ |
| 3.1.8 — No forgot-password endpoint | L1 — V2.5.1 | API2:2023 Broken Authentication | A07:2021 Identification and Authentication Failures | ⬜ |
| 3.2.1 — HttpOnly cookie | L1 — V3.4.1 | API2:2023 Broken Authentication | A02:2021 Cryptographic Failures | ⬜ |
| 3.2.2 — Secure cookie flag in production | L1 — V3.4.2 | API2:2023 Broken Authentication | A02:2021 Cryptographic Failures | ❌ GAP |
| 3.2.3 — SameSite=Lax cookie | L1 — V3.4.3 | API2:2023 Broken Authentication | A01:2021 Broken Access Control | ⬜ |
| 3.2.4 — Explicit Path=/ on cookie | L1 — V3.4.4 | API2:2023 Broken Authentication | A02:2021 Cryptographic Failures | ⬜ |
| 3.2.5 — No session data in localStorage | L1 — V3.4.1 | API2:2023 Broken Authentication | A07:2021 Identification and Authentication Failures | ⬜ |
| 3.2.6 — No token in URL | L1 — V3.1.1 | API2:2023 Broken Authentication | A07:2021 Identification and Authentication Failures | ⬜ |
| 3.2.7 — Session duration acceptable | L2 — V3.3.2 | API2:2023 Broken Authentication | A07:2021 Identification and Authentication Failures | ⬜ |
| 3.2.8 — No refresh token rotation | L2 — V3.3.3 | API2:2023 Broken Authentication | A07:2021 Identification and Authentication Failures | ❌ GAP |
| 3.3.1 — User A cannot access User B's assessment | L1 — V4.1.1 | API1:2023 Broken Object Level Authorization | A01:2021 Broken Access Control | ✅ |
| 3.3.2 — User A cannot download User B's report | L1 — V4.1.1 | API1:2023 Broken Object Level Authorization | A01:2021 Broken Access Control | ✅ |
| 3.3.3 — Admin cannot view assessment data | L2 — V4.1.2 | API1:2023 Broken Object Level Authorization | A01:2021 Broken Access Control | ✅ |
| 3.3.4 — Reviewer: audit logs only | L2 — V4.1.3 | API5:2023 Broken Function Level Authorization | A01:2021 Broken Access Control | ❌ GAP |
| 3.3.5 — User cannot access admin endpoints | L1 — V4.2.1 | API5:2023 Broken Function Level Authorization | A01:2021 Broken Access Control | ⬜ |
| 3.3.6 — API key BOLA isolation | L1 — V4.1.1 | API1:2023 Broken Object Level Authorization | A01:2021 Broken Access Control | ❌ GAP |
| 3.3.7 — Mass assignment prevention | L2 — V4.3.2 | API3:2023 Broken Object Property Level Authorization | A08:2021 Software and Data Integrity Failures | ⬜ |
| 3.4.1 — Parameterized SQL queries | L1 — V5.3.4 | API9:2023 Improper Inventory Management | A03:2021 Injection | ✅ |
| 3.4.2 — No eval/exec on user input | L1 — V5.3.8 | API9:2023 Improper Inventory Management | A03:2021 Injection | ⬜ |
| 3.4.3 — File extension whitelist | L1 — V12.1.1 | API4:2023 Unrestricted Resource Consumption | A05:2021 Security Misconfiguration | ⬜ |
| 3.4.4 — File size limit 5GB | L1 — V12.1.2 | API4:2023 Unrestricted Resource Consumption | A05:2021 Security Misconfiguration | ⬜ |
| 3.4.5 — Magic bytes/MIME verification | L2 — V12.1.3 | API4:2023 Unrestricted Resource Consumption | A05:2021 Security Misconfiguration | ❌ GAP |
| 3.4.6 — ZIP bomb protection | L2 — V12.1.2 | API4:2023 Unrestricted Resource Consumption | A05:2021 Security Misconfiguration | ❌ GAP |
| 3.4.7 — Path traversal prevention | L1 — V12.3.1 | API4:2023 Unrestricted Resource Consumption | A01:2021 Broken Access Control | ✅ |
| 3.4.8 — Jinja2 template autoescape | L1 — V5.3.3 | API9:2023 Improper Inventory Management | A03:2021 Injection | ⬜ |
| 3.4.9 — No dangerouslySetInnerHTML | L1 — V5.3.3 | API9:2023 Improper Inventory Management | A03:2021 Injection | ⬜ |
| 3.4.10 — SSRF webhook URL validation | L2 — V10.3.2 | API7:2023 Server Side Request Forgery | A10:2021 Server-Side Request Forgery | ❌ GAP |
| 3.4.11 — Open redirect prevention | L1 — V5.1.5 | API1:2023 Broken Object Level Authorization | A01:2021 Broken Access Control | ⬜ |
| 3.5.1 — bcrypt cost factor ≥ 12 | L1 — V2.4.1 | API2:2023 Broken Authentication | A02:2021 Cryptographic Failures | ⬜ |
| 3.5.2 — JWT secret minimum entropy | L2 — V2.6.2 | API2:2023 Broken Authentication | A02:2021 Cryptographic Failures | ⬜ |
| 3.5.3 — API key entropy sufficient | L2 — V2.8.4 | API2:2023 Broken Authentication | A02:2021 Cryptographic Failures | ⬜ |
| 3.5.4 — TLS 1.3 at ingress | L1 — V9.1.1 | API8:2023 Security Misconfiguration | A02:2021 Cryptographic Failures | ⬜ |
| 3.5.5 — HSTS header | L2 — V9.1.2 | API8:2023 Security Misconfiguration | A05:2021 Security Misconfiguration | ❌ GAP |
| 3.5.6 — S3 AES-256 encryption | L2 — V9.2.3 | API8:2023 Security Misconfiguration | A02:2021 Cryptographic Failures | ⬜ |
| 3.6.1 — No secrets in docker-compose.yml | L2 — V14.2.1 | API8:2023 Security Misconfiguration | A05:2021 Security Misconfiguration | ⬜ |
| 3.6.2 — No secrets in K8s manifests | L2 — V14.2.1 | API8:2023 Security Misconfiguration | A05:2021 Security Misconfiguration | ❌ GAP |
| 3.6.3 — Non-root Docker user | L2 — V14.2.3 | API8:2023 Security Misconfiguration | A05:2021 Security Misconfiguration | ❌ GAP |
| 3.6.4 — Read-only root filesystem | L3 — V14.2.4 | API8:2023 Security Misconfiguration | A05:2021 Security Misconfiguration | ❌ GAP |
| 3.6.5 — K8s Pod Security Standards | L3 — V14.2.3 | API8:2023 Security Misconfiguration | A05:2021 Security Misconfiguration | ❌ GAP |
| 3.6.6 — K8s NetworkPolicy isolation | L2 — V14.4.5 | API8:2023 Security Misconfiguration | A05:2021 Security Misconfiguration | ❌ GAP |
| 3.6.7 — Redis requirepass | L2 — V14.4.2 | API8:2023 Security Misconfiguration | A05:2021 Security Misconfiguration | ❌ GAP |
| 3.6.8 — PostgreSQL scram-sha-256 | L2 — V14.4.3 | API8:2023 Security Misconfiguration | A05:2021 Security Misconfiguration | ⬜ |
| 3.6.9 — AWS S3 bucket not public | L1 — V14.4.1 | API8:2023 Security Misconfiguration | A05:2021 Security Misconfiguration | ⬜ |
| 3.6.10 — CORS no wildcard | L1 — V14.5.3 | API8:2023 Security Misconfiguration | A05:2021 Security Misconfiguration | ⬜ |
| 3.7.1 — No secrets in CI logs | L2 — V14.2.1 | API8:2023 Security Misconfiguration | A05:2021 Security Misconfiguration | ⬜ |
| 3.7.2 — npm audit in CI | L2 — V14.2.2 | API6:2023 Unrestricted Access to Sensitive Business Flows | A06:2021 Vulnerable and Outdated Components | ❌ GAP |
| 3.7.3 — Bandit SAST in CI | L2 — V14.3.2 | API9:2023 Improper Inventory Management | A06:2021 Vulnerable and Outdated Components | ❌ GAP |
| 3.7.4 — Container scanning before deploy | L2 — V14.2.2 | API8:2023 Security Misconfiguration | A06:2021 Vulnerable and Outdated Components | ❌ GAP |
| 3.7.5 — Docs disabled in production | L1 — V14.3.2 | API9:2023 Improper Inventory Management | A05:2021 Security Misconfiguration | ⬜ |
| 3.8.1 — Security events in audit_logs | L2 — V7.1.1 | API8:2023 Security Misconfiguration | A09:2021 Security Logging and Monitoring Failures | ⬜ |
| 3.8.2 — Alerting on failure rate | L2 — V7.2.2 | API8:2023 Security Misconfiguration | A09:2021 Security Logging and Monitoring Failures | ⬜ |
| 3.8.3 — Webhook failure monitoring | L2 — V7.2.1 | API8:2023 Security Misconfiguration | A09:2021 Security Logging and Monitoring Failures | ⬜ |
| 3.8.4 — Incident response plan | L2 — V17.1.1 | API8:2023 Security Misconfiguration | A09:2021 Security Logging and Monitoring Failures | ❌ GAP |
| 3.8.5 — Security disclosure policy | L2 — V17.1.2 | API8:2023 Security Misconfiguration | A09:2021 Security Logging and Monitoring Failures | ❌ GAP |

---

## 7. Hardening Guides by Component

---

### 7.1 PostgreSQL (ref TDD §6 DDL)

```sql
-- ── Step 1: Create separate roles per service ──────────────────────────────

-- API role: reads all tables, writes submissions and metadata
CREATE ROLE toolkit_api LOGIN PASSWORD '${TOOLKIT_API_DB_PASSWORD}';
GRANT SELECT, INSERT, UPDATE ON TABLE
    assessments, dataset_metadata, dataset_profiles, domain_scores,
    assessment_results, audit_logs, users, api_keys
TO toolkit_api;

-- Worker role: reads assessments/metadata, writes results and profiles
CREATE ROLE toolkit_worker LOGIN PASSWORD '${TOOLKIT_WORKER_DB_PASSWORD}';
GRANT SELECT ON TABLE assessments, dataset_metadata TO toolkit_worker;
GRANT SELECT, INSERT, UPDATE ON TABLE
    dataset_profiles, domain_scores, assessment_results, audit_logs
TO toolkit_worker;
GRANT UPDATE (status, completion_timestamp, error_message, error_traceback, celery_task_id)
    ON TABLE assessments TO toolkit_worker;

-- Read-only role for audit queries and Grafana dashboards
CREATE ROLE toolkit_readonly LOGIN PASSWORD '${TOOLKIT_READONLY_DB_PASSWORD}';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO toolkit_readonly;

-- ── Step 2: Revoke public schema permissions ───────────────────────────────

REVOKE CREATE ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON DATABASE toolkit_db FROM PUBLIC;

-- ── Step 3: Enable scram-sha-256 password encryption ──────────────────────
-- In postgresql.conf:
-- password_encryption = 'scram-sha-256'
-- Then update all existing users:
ALTER ROLE toolkit_api PASSWORD '${TOOLKIT_API_DB_PASSWORD}';
ALTER ROLE toolkit_worker PASSWORD '${TOOLKIT_WORKER_DB_PASSWORD}';

-- ── Step 4: Block TRUNCATE on audit_logs ──────────────────────────────────
-- Existing rule blocks DELETE; add TRUNCATE protection:
-- Note: PostgreSQL does not support rules on TRUNCATE; use trigger instead:
CREATE OR REPLACE FUNCTION block_audit_truncate()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Truncation of audit_logs is not permitted';
END;
$$;

CREATE TRIGGER no_truncate_audit
BEFORE TRUNCATE ON audit_logs
EXECUTE FUNCTION block_audit_truncate();

-- ── Step 5: Row-Level Security on assessments (defense in depth) ──────────

ALTER TABLE assessments ENABLE ROW LEVEL SECURITY;

-- Policy: each user can only see their own assessments
-- (API enforces this already at app layer; RLS provides defense-in-depth)
CREATE POLICY assessment_owner_policy ON assessments
    USING (user_id = current_setting('app.current_user_id')::uuid);

-- Set app.current_user_id at connection time in SQLAlchemy session:
-- await session.execute(text("SET LOCAL app.current_user_id = :uid"), {"uid": str(user_id)})

-- ── Step 6: Connection and query limits ───────────────────────────────────
-- In postgresql.conf:
-- max_connections = 100
-- statement_timeout = '30s'
-- idle_in_transaction_session_timeout = '60s'
-- log_min_duration_statement = 1000  # Log slow queries > 1s

ALTER ROLE toolkit_api CONNECTION LIMIT 20;
ALTER ROLE toolkit_worker CONNECTION LIMIT 10;

-- ── Step 7: Enable pgaudit for DDL changes ────────────────────────────────
-- In postgresql.conf:
-- shared_preload_libraries = 'pgaudit'
-- pgaudit.log = 'ddl, role, connection'
-- pgaudit.log_catalog = off

-- ── Step 8: SSL enforcement ────────────────────────────────────────────────
-- In postgresql.conf:
-- ssl = on
-- ssl_cert_file = '/etc/ssl/certs/server.crt'
-- ssl_key_file = '/etc/ssl/private/server.key'

-- In pg_hba.conf (replace all 'md5' with 'scram-sha-256'):
-- hostssl  toolkit_db  toolkit_api     0.0.0.0/0   scram-sha-256
-- hostssl  toolkit_db  toolkit_worker  0.0.0.0/0   scram-sha-256
-- local    all         all                         reject
```

---

### 7.2 Redis (ref TDD §22.1)

Add to `redis.conf` (mount as `ConfigMap` in K8s or volume in Docker):

```conf
# ── Authentication ────────────────────────────────────────────────────────
requirepass ${REDIS_PASSWORD}

# ── Disable dangerous commands ────────────────────────────────────────────
rename-command FLUSHALL ""
rename-command FLUSHDB ""
rename-command CONFIG  ""
rename-command DEBUG   ""
rename-command EVAL    ""
rename-command SCRIPT  ""

# ── ACL file (preferred over rename-command in Redis 6+) ─────────────────
aclfile /etc/redis/users.acl

# users.acl content:
# user celery_user on >celery_password ~celery:* &assessment:* &webhook:* +rpush +lpop +lrange +llen +del +expire +get +set +sadd +smembers
# user default off

# ── Memory limits ─────────────────────────────────────────────────────────
maxmemory 1gb
maxmemory-policy allkeys-lfu
lfu-log-factor 10

# ── Persistence ───────────────────────────────────────────────────────────
appendonly yes
appendfsync everysec
no-appendfsync-on-rewrite no

# ── Network binding ───────────────────────────────────────────────────────
bind 127.0.0.1  # K8s: let NetworkPolicy handle isolation; bind to pod IP only
protected-mode yes

# ── TLS (if Redis 6+ with TLS support) ───────────────────────────────────
# tls-port 6380
# tls-cert-file /tls/redis.crt
# tls-key-file /tls/redis.key
# tls-ca-cert-file /tls/ca.crt
```

K8s Redis deployment update:
```yaml
# k8s/redis-deployment.yaml (excerpt)
containers:
  - name: redis
    image: redis:7.2-alpine
    command:
      - redis-server
      - /etc/redis/redis.conf
    securityContext:
      runAsNonRoot: true
      runAsUser: 999   # redis user in alpine image
      runAsGroup: 999
      readOnlyRootFilesystem: true
      capabilities:
        drop: ["ALL"]
    volumeMounts:
      - name: redis-config
        mountPath: /etc/redis
      - name: redis-data
        mountPath: /data
volumes:
  - name: redis-config
    configMap:
      name: redis-config
  - name: redis-data
    persistentVolumeClaim:
      claimName: redis-pvc
```

---

### 7.3 AWS S3 Hardening (ref TDD §7)

```bash
# ── AWS CLI configuration ─────────────────────────────────────────────────
# Configure AWS CLI credentials with necessary IAM permissions
aws configure

# ── Block all public access ───────────────────────────────────────────────
aws s3api put-public-access-block \
  --bucket aikosh-datasets \
  --public-access-block-configuration \
  "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

# Verify:
aws s3api get-public-access-block --bucket aikosh-datasets

# ── Enable bucket versioning (accidental deletion recovery) ───────────────
aws s3api put-bucket-versioning \
  --bucket aikosh-datasets \
  --versioning-configuration Status=Enabled

# ── Enable server access logging ──────────────────────────────────────────
# Configure AWS S3 server access logging target bucket
aws s3api put-bucket-logging \
  --bucket aikosh-datasets \
  --bucket-logging-status file:///tmp/logging.json

# ── Lifecycle policy: expire incomplete multipart uploads after 7 days ────
cat > /tmp/lifecycle.json << 'EOF'
{
  "Rules": [
    {
      "ID": "expire-incomplete-multipart",
      "Status": "Enabled",
      "Filter": {"Prefix": "uploads/"},
      "AbortIncompleteMultipartUpload": {"DaysAfterInitiation": 7}
    },
    {
      "ID": "expire-temp-profiles",
      "Status": "Enabled",
      "Filter": {"Prefix": "profiles/"},
      "Expiration": {"Days": 365}
    }
  ]
}
EOF
aws s3api put-bucket-lifecycle-configuration \
  --bucket aikosh-datasets \
  --lifecycle-configuration file:///tmp/lifecycle.json

# ── Bucket policy: deny dangerous content types on upload ─────────────────
# Enforce via pre-signed URL conditions (ContentType) in s3_client.py:
# Add to generate_presigned_post(): Conditions=[['eq', '$Content-Type', 'text/csv']]

# ── S3 Credentials: K8s Secret (not .env) ────────────────────────────
kubectl create secret generic s3-credentials \
  --from-literal=S3_ACCESS_KEY=${S3_ACCESS_KEY} \
  --from-literal=S3_SECRET_KEY=${S3_SECRET_KEY} \
  -n toolkit-prod

# ── S3 server-side encryption (production AWS S3) ─────────────────────────
aws s3api put-bucket-encryption \
  --bucket aikosh-toolkit-bucket \
  --server-side-encryption-configuration \
  '{"Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]}'

# Verify:
aws s3api get-bucket-encryption --bucket aikosh-toolkit-bucket
```

In `backend/app/storage/s3_client.py` — add `ContentLengthRange` to pre-signed upload:
```python
# Replace generate_presigned_url() with generate_presigned_post() for uploads
def generate_upload_presigned_post(key: str, max_size_bytes: int = 5_368_709_120) -> dict:
    return s3_client.generate_presigned_post(
        Bucket=settings.S3_BUCKET_NAME,
        Key=key,
        Conditions=[
            ["content-length-range", 1, max_size_bytes],
            ["starts-with", "$Content-Type", ""],
        ],
        ExpiresIn=3600  # 1h upload window
    )
```

---

### 7.4 Docker (ref TDD §22.1)

```dockerfile
# backend/Dockerfile — full hardened version

FROM python:3.11-slim AS base

# ── Security: create non-root user ────────────────────────────────────────
RUN groupadd --gid 1000 appgroup \
    && useradd --uid 1000 --gid 1000 --no-create-home --shell /bin/false appuser

WORKDIR /app

# ── Install dependencies as root (need write to system paths) ─────────────
COPY --chown=appuser:appgroup requirements.txt .
RUN pip install --no-cache-dir --require-hashes -r requirements.txt

# ── Copy app code with correct ownership ─────────────────────────────────
COPY --chown=appuser:appgroup . .

# ── Drop to non-root user ─────────────────────────────────────────────────
USER appuser

# ── Healthcheck ───────────────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/api/v1/health')" || exit 1

# ── API service CMD ───────────────────────────────────────────────────────
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

```dockerfile
# frontend/Dockerfile — full hardened version

FROM node:20-alpine AS builder
RUN addgroup --gid 1000 appgroup \
    && adduser --uid 1000 --gid 1000 --disabled-password --gecos "" appuser

WORKDIR /app
COPY --chown=appuser:appgroup package*.json ./
RUN npm ci --only=production
COPY --chown=appuser:appgroup . .
RUN npm run build

FROM node:20-alpine AS runner
RUN addgroup --gid 1000 appgroup \
    && adduser --uid 1000 --gid 1000 --disabled-password --gecos "" appuser

WORKDIR /app
COPY --from=builder --chown=appuser:appgroup /app/.next/standalone ./
COPY --from=builder --chown=appuser:appgroup /app/.next/static ./.next/static
COPY --from=builder --chown=appuser:appgroup /app/public ./public

USER appuser
EXPOSE 3000
CMD ["node", "server.js"]
```

Docker run flags for production:
```bash
# API container — read-only with tmpfs for any necessary temp writes
docker run \
  --read-only \
  --tmpfs /tmp:size=64m \
  --security-opt no-new-privileges \
  --cap-drop ALL \
  -e ENVIRONMENT=production \
  toolkit-api:latest

# Worker container — needs writable /tmp for dataset processing
docker run \
  --read-only \
  --tmpfs /tmp:size=5g \        # Dataset processing up to 5GB
  --security-opt no-new-privileges \
  --cap-drop ALL \
  toolkit-worker:latest
```

---

### 7.5 Kubernetes (ref TDD §22.2)

```yaml
# k8s/security-context-patch.yaml
# Apply to ALL pod specs (api, worker-assessment, worker-webhook, frontend)

securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  runAsGroup: 1000
  fsGroup: 1000
  readOnlyRootFilesystem: true
  seccompProfile:
    type: RuntimeDefault
  capabilities:
    drop: ["ALL"]
  allowPrivilegeEscalation: false
```

```yaml
# k8s/network-policies.yaml — complete network isolation

apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-default
  namespace: toolkit-prod
spec:
  podSelector: {}
  policyTypes: [Ingress, Egress]
  # No ingress or egress rules = deny everything by default

---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-api-ingress
  namespace: toolkit-prod
spec:
  podSelector:
    matchLabels:
      app: toolkit-api
  policyTypes: [Ingress, Egress]
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: ingress-nginx
      ports:
        - protocol: TCP
          port: 8000
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: postgres
      ports:
        - protocol: TCP
          port: 5432
    - to:
        - podSelector:
            matchLabels:
              app: redis
      ports:
        - protocol: TCP
          port: 6379
    - to:
        - ipBlock:
            cidr: 0.0.0.0/0
      ports:
        - protocol: TCP
          port: 443

---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-worker-assessment
  namespace: toolkit-prod
spec:
  podSelector:
    matchLabels:
      app: worker-assessment
  policyTypes: [Egress]
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: postgres
      ports:
        - protocol: TCP
          port: 5432
    - to:
        - podSelector:
            matchLabels:
              app: redis
      ports:
        - protocol: TCP
          port: 6379
    - to:
        - ipBlock:
            cidr: 0.0.0.0/0
      ports:
        - protocol: TCP
          port: 443

---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-worker-webhook-egress
  namespace: toolkit-prod
spec:
  podSelector:
    matchLabels:
      app: worker-webhook
  policyTypes: [Egress]
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: redis
      ports:
        - protocol: TCP
          port: 6379
    # Allow outbound HTTPS to AIKosh webhook endpoint only
    - ports:
        - protocol: TCP
          port: 443
      to:
        - ipBlock:
            cidr: 0.0.0.0/0
            except:
              - 10.0.0.0/8
              - 172.16.0.0/12
              - 192.168.0.0/16
              - 169.254.0.0/16
              - 127.0.0.0/8

---
# K8s Secrets (replace .env pattern for production)
apiVersion: v1
kind: Secret
metadata:
  name: toolkit-secrets
  namespace: toolkit-prod
type: Opaque
stringData:
  JWT_SECRET: "${JWT_SECRET}"
  DB_PASSWORD_API: "${TOOLKIT_API_DB_PASSWORD}"
  DB_PASSWORD_WORKER: "${TOOLKIT_WORKER_DB_PASSWORD}"
  REDIS_PASSWORD: "${REDIS_PASSWORD}"
  S3_ACCESS_KEY: "${S3_ACCESS_KEY}"
  S3_SECRET_KEY: "${S3_SECRET_KEY}"
  AIKOSH_WEBHOOK_SECRET: "${AIKOSH_WEBHOOK_SECRET}"

```

```bash
# Apply namespace Pod Security Standards
kubectl label namespace toolkit-prod \
  pod-security.kubernetes.io/enforce=restricted \
  pod-security.kubernetes.io/warn=restricted \
  pod-security.kubernetes.io/audit=restricted

# Apply network policies
kubectl apply -f k8s/network-policies.yaml

# Verify network policies active
kubectl get networkpolicies -n toolkit-prod

# Verify pod security admission
kubectl describe namespace toolkit-prod | grep pod-security
```

---

### 7.6 FastAPI (`backend/app/main.py`)

```python
# backend/app/main.py — complete hardened configuration

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.gzip import GZipMiddleware
from app.api.v1 import assess, reports, datasets, health, auth, admin
from app.config import settings

# Conditionally disable interactive docs in production
app = FastAPI(
    title="AIKosh Dataset Quality Toolkit",
    version="1.0.0",
    docs_url=None if settings.ENVIRONMENT == "production" else "/docs",
    redoc_url=None if settings.ENVIRONMENT == "production" else "/redoc",
    openapi_url=None if settings.ENVIRONMENT == "production" else "/openapi.json",
)

# ── Middleware: ordered from outermost to innermost ─────────────────────────

# 1. HTTPS redirect (outermost — redirect before any processing)
if settings.ENVIRONMENT == "production":
    app.add_middleware(HTTPSRedirectMiddleware)

# 2. Trusted host validation (blocks Host header injection)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,  # e.g. ["toolkit.aikosh.gov.in"]
)

# 3. CORS — configured origins only, never wildcard
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
)

# 4. GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 5. Security headers middleware (innermost — set on every response)
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)

    # HSTS: only on HTTPS in production
    if settings.ENVIRONMENT == "production":
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )

    # Prevent MIME sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"

    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"

    # Content Security Policy
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "frame-ancestors 'none'"
    )

    # Legacy XSS protection (IE/older browsers)
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # Remove server identification headers
    response.headers.pop("server", None)
    response.headers.pop("x-powered-by", None)

    # Prevent caching of sensitive responses
    if request.url.path.startswith("/api/v1/auth") or \
       request.url.path.startswith("/api/v1/assess"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["Pragma"] = "no-cache"

    return response

# ── Request size limiter ────────────────────────────────────────────────────
@app.middleware("http")
async def limit_request_body(request: Request, call_next):
    # Non-upload endpoints: 1MB body limit
    if not request.url.path.startswith("/api/v1/assess/upload"):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 1_048_576:  # 1MB
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=413,
                content={"error": "request_too_large", "message": "Request body exceeds 1MB limit"}
            )
    return await call_next(request)

# ── Routers ────────────────────────────────────────────────────────────────
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(auth.router, prefix="/api/v1", tags=["authentication"])
app.include_router(admin.router, prefix="/api/v1", tags=["admin"])
app.include_router(assess.router, prefix="/api/v1", tags=["assessment"])
app.include_router(reports.router, prefix="/api/v1", tags=["reports"])
app.include_router(datasets.router, prefix="/api/v1", tags=["datasets"])
```

---

### 7.7 Next.js Frontend (`frontend/next.config.ts`)

```typescript
// frontend/next.config.ts — complete hardened configuration

import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  // Disable server identification header
  poweredByHeader: false,

  // Output standalone build for minimal Docker image
  output: 'standalone',

  // Security headers on all routes
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=31536000; includeSubDomains; preload',
          },
          {
            key: 'Content-Security-Policy',
            value: [
              "default-src 'self'",
              "script-src 'self'",           // No inline scripts
              "style-src 'self' 'unsafe-inline'",  // Tailwind requires inline styles
              "img-src 'self' data:",
              "font-src 'self'",
              "connect-src 'self'",           // API calls to same origin only
              "frame-ancestors 'none'",
              "base-uri 'self'",
              "form-action 'self'",
            ].join('; '),
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=(), payment=()',
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
        ],
      },
      // Additional: prevent caching of auth/assessment pages
      {
        source: '/(login|register|upload|dashboard)/(.*)?',
        headers: [
          {
            key: 'Cache-Control',
            value: 'no-store, no-cache, must-revalidate',
          },
        ],
      },
    ]
  },

  // API proxy: route /api/* to backend — avoids CORS preflight from browser
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL}/api/:path*`,
      },
    ]
  },
}

export default nextConfig
```

```bash
# Verify no dangerouslySetInnerHTML usage in frontend codebase
grep -rn "dangerouslySetInnerHTML" frontend/
# Expected: zero results

# Verify no direct token access in JS (localStorage/sessionStorage)
grep -rn "localStorage\|sessionStorage" frontend/
# Expected: zero results

# Verify API client uses credentials: include for cookie transport
grep -n "credentials" frontend/lib/api/client.ts
# Expected: credentials: 'include' on all fetch calls
```

---

## 8. Appendix — Mapped Documentation References

| Security Concern | Documented In | Section / Location |
|---|---|---|
| Dual-auth model (JWT cookie + Bearer API key) | TDD v1.1, OpenAPI v1.1, AGENTS.md | TDD §17, OpenAPI §3, AGENTS.md §4 |
| Cookie flags (`HttpOnly`, `Secure`, `SameSite`, `Path`) | TDD v1.1, OpenAPI v1.1 | TDD §17.1, OpenAPI §3.1 |
| `secure=False` gap in `auth.py:69` | OpenAPI v1.1 comment, TDD §17.1 | OpenAPI §3.1, TDD §17.1 |
| JWT HS256 algorithm, 30-day expiry, no refresh | TDD v1.1, OpenAPI v1.1 | TDD §17.1–17.4, OpenAPI §3.1 |
| API key format `tkt_live_{32chars}`, SHA-256 storage | TDD v1.1, OpenAPI v1.1 | TDD §17.2, OpenAPI §3.2 |
| Rate limiting (100 req/min API, 5/min login per IP) | TDD v1.1, OpenAPI v1.1 | TDD §20, OpenAPI §5 |
| BOLA enforcement and existing tests | `backend/tests/test_auth_bola.py` | Full file; TDD §17.3 |
| File upload validation (MIME, magic bytes, size, path) | TDD v1.1 | TDD §20 |
| ZIP file and multiformat support | TDD v1.1, PRD v1.1 | TDD §5.3, PRD §23 |
| CORS restricted to `settings.CORS_ORIGINS` | TDD v1.1, AGENTS.md | TDD §20, AGENTS.md §9 |
| SQLAlchemy parameterized queries — no raw SQL | TDD v1.1 | TDD §20 |
| Audit log append-only (`CREATE RULE no_delete_audit`) | TDD v1.1 DDL | TDD §6.1 (DDL), PRD §26 |
| Audit log SHA-256 chaining for tamper detection | TDD v1.1 | TDD §18 |
| `pip-audit` in CI/CD | TDD v1.1 | TDD §20 |
| Password policy regex `^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)(?=.*[@$!%*?&])...` | OpenAPI v1.1 | OpenAPI §7 YAML `/api/v1/auth/register` |
| Pre-signed URL 24h expiry for reports | TDD v1.1, OpenAPI v1.1 | TDD §7, OpenAPI §7.3 |
| Upload flow mismatch (multipart vs. pre-signed URL target) | OpenAPI v1.1 | OpenAPI §7.2 `IMPORTANT` note |
| Encryption at rest (AES-256 S3, PostgreSQL tablespace) | TDD v1.1, PRD v1.1 | TDD §20, PRD §25 |
| Encryption in transit (TLS 1.3 via Nginx/Ingress) | TDD v1.1, PRD v1.1 | TDD §20, PRD §25 |
| File isolation per Celery task (unique temp dir) | TDD v1.1 | TDD §20 |
| No raw dataset content in DB — only statistics | TDD v1.1 | TDD §20, §7 |
| Admin cannot access datasets or reports (hard boundary) | TDD v1.1, OpenAPI v1.1, PRD v1.1 | TDD §17.3, OpenAPI §3.3, PRD §25 |
| Celery task limits (soft 300s, hard 360s) | TDD v1.1 | TDD §5.2 |
| Webhook retry schedule (3×: 30s, 120s, 480s) | TDD v1.1, OpenAPI v1.1 | TDD §5.8, OpenAPI §8 |
| DPDP Act 2023 compliance requirement | TDD v1.1, PRD v1.1 | TDD §20, PRD §25 |
| Data sensitivity classification (Q21 — standard/high_stigma/critical) | Questionnaire v1.1 | Q21, Section E |
| De-identification methods (Q23–Q25: HIPAA, k-anonymity, DP) | Questionnaire v1.1 | Q23–Q25, Section E |
| PRS multipliers (1.0×, 1.5×, 2.0×) from MIDAS Annexure I | PRD v1.1, OpenAPI v1.1 | PRD §3.5, OpenAPI §10 (Sensitivity Class enum) |
| K8s HPA config for `worker-assessment` (3–20 replicas) | TDD v1.1 | TDD §22.2 |
| Docker Compose service definitions | TDD v1.1 | TDD §22.1 |
| Flower monitoring on port 5555 (no auth documented) | TDD v1.1 | TDD §22.1, §24 |
| structlog structured JSON logging | TDD v1.1 | TDD §3 (Technology Stack) |
| Prometheus + Grafana monitoring | TDD v1.1 | TDD §24 |
| `backend/app/config.py` — all settings via Pydantic Settings | TDD v1.1 | TDD §21 |
| `.env.example` in TDD showing placeholder values | TDD v1.1 | TDD §21 |
| No CSP, HSTS, X-Content-Type-Options, X-Frame-Options | Not in any document | Gap identified in audit |
| No CSRF token (relies on SameSite=Lax only) | Not in any document | Gap identified in audit |
| No K8s NetworkPolicy | TDD v1.1 (gap noted) | TDD §22.2 gap list |
| No K8s Secrets management (uses .env approach) | TDD v1.1 (gap noted) | TDD §22.2 gap list |
| No incident response plan | Not in any document | Gap identified in audit |
| No SAST (Bandit/ESLint) in CI | Not in any document | Gap identified in audit |
| No npm audit in CI | Not in any document (only pip-audit mentioned) | TDD §20 |
| No container image scanning (Trivy) | Not in any document | Gap identified in audit |
| No secret scanning in git (TruffleHog) | Not in any document | Gap identified in audit |
| No API fuzzing (Schemathesis) | Not in any document | Gap identified in audit |
| No concurrency/race condition tests | Not in any document | Gap identified in audit |
| No load tests (Locust/JMeter) | Not in any document | Gap identified in audit |
| No cookie security tests in CI | Not in any document | Gap identified in audit |
| No magic bytes automated test | TDD §20 (documented only, no test) | TDD §20 |
| No S3 direct URL access test | Not in any document | Gap identified in audit |
| No RLS/direct DB access test | Not in any document | Gap identified in audit |

---

*End of Document*

---

**Document History**

| Version | Date | Author | Notes |
|---|---|---|---|
| 1.0 | June 25, 2026 | — | Initial security audit checklist. Covers all 10 STRIDE layers, 28-row automated testing matrix, 8-category manual review, full CI/CD workflow, P0–P3 remediation matrix, OWASP mapping, and 7-component hardening guides. |
