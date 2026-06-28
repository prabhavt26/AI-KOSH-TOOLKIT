# Remaining Work — AIKosh Dataset Quality Evaluation Toolkit

**Last Updated:** 28 Jun 2026  
**Source Documents:**
- [`SECURITY_AUDIT_CHECKLIST.md`](./SECURITY_AUDIT_CHECKLIST.md)
- [`BUGS_AND_GAPS.md`](./BUGS_AND_GAPS.md)
- [`OpenAPI.md`](./OpenAPI.md)
- [`PRD_AIKosh_Dataset_Quality_Toolkit.md`](./PRD_AIKosh_Dataset_Quality_Toolkit.md)
- [`TDD_AIKosh_Dataset_Quality_Toolkit.md`](./TDD_AIKosh_Dataset_Quality_Toolkit.md)

Every item below references its source document section. Verified by reading the actual file.

---

## 1. Security Test Files (14 files)

Source: [`SECURITY_AUDIT_CHECKLIST.md §2 — Automated Security Testing Matrix`](./SECURITY_AUDIT_CHECKLIST.md#2-automated-security-testing-matrix) and [`BUGS_AND_GAPS.md P3.8`](./BUGS_AND_GAPS.md#p38-missing-security-tests-14-files).

| # | Test File | What It Tests | Source §2 Row |
|---|---|---|---|
| 1 | `backend/tests/test_cors.py` | Preflight from `https://evil.example.com` returns no CORS headers | item 24 — CORS restrictive origins |
| 2 | `backend/tests/test_cookie_security.py` | HttpOnly, Secure (prod only), SameSite=Lax, Path=/ on Set-Cookie | item 14 — Cookie security flags |
| 3 | `backend/tests/test_file_upload_security.py` | Magic bytes mismatch → 422; size > 5GB → 413; path traversal → 422; ZIP bomb → 413 | item 15 — File upload security |
| 4 | `backend/tests/test_sql_injection.py` | SQL metacharacters in string fields produce no unexpected results | item 16 — SQL injection unit |
| 5 | `backend/tests/test_concurrency.py` | 10 simultaneous submissions — all isolated, no race conditions | item 17 — Concurrency / race conditions |
| 6 | `backend/tests/test_rate_limiting.py` | 101st request in 60s → 429 with `Retry-After` and `X-RateLimit-Remaining: 0` | item 21 — Rate limiting |
| 7 | `backend/tests/test_csrf.py` | Cross-origin POST without matching Origin → rejected by CORS | item 22 — CSRF protection |
| 8 | `backend/tests/test_audit_append_only.py` | DELETE returns 0 rows; TRUNCATE raises error (needs TRUNCATE trigger first) | item 23 — Audit log append-only |
| 9 | `backend/tests/test_s3_security.py` | Expired pre-signed URL → 403; direct key access → 403 | item 20 — S3 direct access |
| 10 | `backend/tests/test_auth_bypass.py` | No cookie/Bearer → 401; tampered JWT → 401 | item 25 — Auth bypass |
| 11 | `backend/tests/test_webhook_retry.py` | Mock 5xx → exactly 3 retries at correct backoff (30s/120s/480s) | item 27 — Webhook retry |
| 12 | `backend/tests/test_health_endpoint.py` | Unauthenticated call sees only `{"status":"healthy"}`; no deps/version leak | item 28 — Health endpoint data leak |
| 13 | `backend/tests/test_reviewer_access.py` | Reviewer sees audit logs but NOT assessment results | [`§3.3.4`](./SECURITY_AUDIT_CHECKLIST.md#33-access-control-bolaidor) |
| 14 | `backend/tests/test_celery_pipeline.py` | Full E2E pipeline test (file exists, verify status) | [`BUGS.md § E2E Verification Checklist`](./BUGS_AND_GAPS.md#e2e-verification-checklist) |

---

## 2. Infrastructure Hardening (14 items)

Source: [`BUGS_AND_GAPS.md § P2 — Architectural Drift & Security Hardening`](./BUGS_AND_GAPS.md#p2--architectural-drift--security-hardening) and [`SECURITY_AUDIT_CHECKLIST.md §1 — Threat Model`](./SECURITY_AUDIT_CHECKLIST.md#1-threat-model-stride-per-layer) and [`§7 — Hardening Guides`](./SECURITY_AUDIT_CHECKLIST.md#7-hardening-guides-by-component).

| # | Item | Details | Source |
|---|---|---|---|
| 15 | **Backend Dockerfile: non-root user** | `backend/Dockerfile` has no `USER` directive — runs as root. Add `adduser` + `USER appuser`. (Frontend Dockerfile already has this.) | [`BUGS.md P3.2`](./BUGS_AND_GAPS.md#p32-no-non-root-user-in-dockerfiles), [`SEC.md §3.6.3`](./SECURITY_AUDIT_CHECKLIST.md#36-infrastructure--configuration) |
| 16 | **k8s Redis: requirepass + PVC** | Redis deployment has no `--requirepass` and uses `emptyDir` (data lost on restart). Add password + `PersistentVolumeClaim`. | [`BUGS.md P2.1`](./BUGS_AND_GAPS.md#p21-k8s-redis-no-password-set), [`P2.4`](./BUGS_AND_GAPS.md#p24-redis-emptydir-in-k8s-no-persistence), [`SEC.md §1.6`](./SECURITY_AUDIT_CHECKLIST.md#16-message-broker-redis-72--backendappworkercelery_apppy) |
| 17 | **k8s MinIO: add StatefulSet** | No MinIO manifest exists, but `S3_ENDPOINT_URL=http://minio:9000` is hardcoded in k8s YAMLs — won't resolve. | [`BUGS.md P2.2`](./BUGS_AND_GAPS.md#p22-no-minio-deployment-in-k8s) |
| 18 | **k8s Flower: add Deployment + Service** | No Flower manifest; docker-compose has Flower on port 5555 for Celery monitoring. | [`BUGS.md P2.3`](./BUGS_AND_GAPS.md#p23-no-flower-deployment-in-k8s), [`SEC.md §1.6`](./SECURITY_AUDIT_CHECKLIST.md#16-message-broker-redis-72--backendappworkercelery_apppy) |
| 19 | **k8s Secrets: use secretKeyRef** | `JWT_SECRET`, `S3_ACCESS_KEY`, etc. hardcoded as `value:` in YAMLs — committed to git. | [`BUGS.md P2.5`](./BUGS_AND_GAPS.md#p25-hardcoded-secrets-in-all-yamls), [`SEC.md §3.6.2`](./SECURITY_AUDIT_CHECKLIST.md#36-infrastructure--configuration) |
| 20 | **k8s NetworkPolicy: create policy** | No `NetworkPolicy` exists — any pod can reach any service. | [`BUGS.md P2.12`](./BUGS_AND_GAPS.md#p212-no-networkpolicy-in-k8s), [`SEC.md §1.8 item 136`](./SECURITY_AUDIT_CHECKLIST.md#18-orchestration-kubernetes--k8s), [`§3.6.6`](./SECURITY_AUDIT_CHECKLIST.md#36-infrastructure--configuration) |
| 21 | **k8s Ingress: split `ingress.yaml`** | Single file contains Ingress + Frontend Deployment + Service — misnamed. Split into 3 files. | [`BUGS.md P2.6`](./BUGS_AND_GAPS.md#p26-ingressyaml-contains-3-unrelated-resources) |
| 22 | **k8s HPA for API** | Only `worker-assessment` has HPA. API has 1 static replica — no auto-scale under load. | [`BUGS.md P2.11`](./BUGS_AND_GAPS.md#p211-no-hpa-for-api-deployment-in-k8s), [`SEC.md §1.8 item 138`](./SECURITY_AUDIT_CHECKLIST.md#18-orchestration-kubernetes--k8s) |
| 23 | **k8s PodSecurity label** | No `pod-security.kubernetes.io/enforce=restricted` label on namespace. | [`SEC.md §3.6.5`](./SECURITY_AUDIT_CHECKLIST.md#36-infrastructure--configuration) |
| 24 | **k8s securityContext on all pods** | Missing `runAsNonRoot`, `readOnlyRootFilesystem`, `capabilities.drop: ["ALL"]`, `allowPrivilegeEscalation: false`. | [`SEC.md §7.5`](./SECURITY_AUDIT_CHECKLIST.md#75-kubernetes-ref-tdd-222) |
| 25 | **Audit TRUNCATE trigger** | `CREATE RULE no_delete_audit` exists but does not block `TRUNCATE`. Add trigger function `block_audit_truncate()`. | [`BUGS.md P3.7`](./BUGS_AND_GAPS.md#p37-no-audit-log-truncate-protection), [`SEC.md §7.1 "Step 4"`](./SECURITY_AUDIT_CHECKLIST.md#71-postgresql-ref-tdd-6-ddl) |
| 26 | **Redis hardening config** | No `rename-command FLUSHALL ""`, ACL, `maxmemory`, or `protected-mode` in docker-compose or k8s. | [`SEC.md §7.2`](./SECURITY_AUDIT_CHECKLIST.md#72-redis-ref-tdd-221) |
| 27 | **`docker-compose.prod.yml`** | No production Docker composition exists — dev compose exposes ports to host, writable FS. | [`BUGS.md P3.3`](./BUGS_AND_GAPS.md#p33-no-docker-composeprodyml) |
| 28 | **MinIO bucket versioning** | Not enabled on `aikosh-datasets` bucket — reports can be overwritten. | [`BUGS.md P3.1`](./BUGS_AND_GAPS.md#p31-no-minio-bucket-versioning), [`SEC.md §7.3`](./SECURITY_AUDIT_CHECKLIST.md#73-minio--s3-ref-tdd-7) |

---

## 3. CI/CD Pipeline (4 items)

Source: [`BUGS.md P3.4`](./BUGS_AND_GAPS.md#p34-no-cicd-github-directory-missing), [`SEC.md §4`](./SECURITY_AUDIT_CHECKLIST.md#4-cicd-pipeline-integration).

`.github/` directory does not exist at project root.

| # | Item | Source |
|---|---|---|
| 29 | Create `.github/workflows/security-scan.yml` with 10 jobs: Bandit, ESLint, tsc, pip-audit, npm audit, Trivy, TruffleHog, pytest security tests, Schemathesis, ZAP, Locust, kube-bench | [`SEC.md §4`](./SECURITY_AUDIT_CHECKLIST.md#4-cicd-pipeline-integration) (full YAML lines 327–753) |
| 30 | Create `bandit` config (`.bandit.yml`) | [`SEC.md §3.7.3`](./SECURITY_AUDIT_CHECKLIST.md#37-cicd-security) |
| 31 | Create ESLint security config (`.eslintrc.security.json`) | [`SEC.md §3.7.3`](./SECURITY_AUDIT_CHECKLIST.md#37-cicd-security) |
| 32 | Create Locust load test file (`backend/tests/load/locustfile.py`) — 100 concurrent users | [`SEC.md §2 item 18`](./SECURITY_AUDIT_CHECKLIST.md#2-automated-security-testing-matrix) |

---

## 4. Schema / Validation Enhancements (5 items)

Source: [`BUGS.md P2.7–P2.10`](./BUGS_AND_GAPS.md#p27-questionnaire-gate-booleans-missing-from-metadataform), [`SEC.md §3.1.7`](./SECURITY_AUDIT_CHECKLIST.md#31-authentication).

| # | Item | Details | Source |
|---|---|---|---|
| 33 | **Gate booleans on MetadataForm** | Add `has_annotated_data`, `has_synthetic_data`, `has_ethics_approval`, `has_named_steward`, `has_linked_models` — frontend tracks these in local state only, never sent to API. | [`BUGS.md P2.7`](./BUGS_AND_GAPS.md#p27-questionnaire-gate-booleans-missing-from-metadataform) |
| 34 | **Add missing study_type options** | Add `"epidemiological_surveillance"`, `"biobank"` to the `Literal` enum in `metadata_form.py`. | [`BUGS.md P2.8`](./BUGS_AND_GAPS.md#p28-study_type-enum-missing-options-from-questionnaire) |
| 35 | **license_type → Literal enum** | Currently bare `str`. Change to `Literal["CC_BY_4", "CC_BY_NC_4", "CC_BY_NC_ND_4", "CC_BY_SA_4", "GODL_INDIA", "RESTRICTED_DUA", "PROPRIETARY", "NOT_DECIDED"]` per Questionnaire Q5. | [`BUGS.md P2.9`](./BUGS_AND_GAPS.md#p29-license_type-should-be-enum-not-free-text) |
| 36 | **Registration rate limit** | Login has rate limiter; register endpoint does not — bot can spam accounts. | [`BUGS.md P2.10`](./BUGS_AND_GAPS.md#p210-no-rate-limiting-on-registration-enumeration-vector) |
| 37 | **Email enumeration fix** | Registration returns different response for existing vs new email. Use constant-time path. | [`SEC.md §3.1.7`](./SECURITY_AUDIT_CHECKLIST.md#31-authentication) |

---

## 5. Security Headers / Middleware (2 items)

| # | Item | Details | Source |
|---|---|---|---|
| 38 | **Add CSP header** | `SecurityHeadersMiddleware` has X-Content-Type-Options, X-Frame-Options, HSTS — but no `Content-Security-Policy: default-src 'self'`. | [`SEC.md §1.2 item 52`](./SECURITY_AUDIT_CHECKLIST.md#12-api-layer-fastapi--backendapp), [`§5 P0`](./SECURITY_AUDIT_CHECKLIST.md#5-remediation-priority-matrix) |
| 39 | **Health endpoint gating** | Public sees `{"status":"healthy"}` only. Full dependency map returned only with `X-Internal-Request: true` header. | [`SEC.md §3.3 item 793`](./SECURITY_AUDIT_CHECKLIST.md#33-access-control-bolaidor), [`§2 item 28`](./SECURITY_AUDIT_CHECKLIST.md#2-automated-security-testing-matrix) |

---

## 6. Documentation (4 items)

| # | Item | Details | Source |
|---|---|---|---|
| 40 | **Create `SECURITY.md`** | Responsible disclosure contact, GPG key, SLA for response at repo root. | [`SEC.md §3.8.5`](./SECURITY_AUDIT_CHECKLIST.md#38-monitoring--incident-response) |
| 41 | **Create `docs/INCIDENT_RESPONSE.md`** | Runbooks: JWT secret leak, S3 misconfiguration, DB compromise, webhook secret exposure. | [`SEC.md §3.8.4`](./SECURITY_AUDIT_CHECKLIST.md#38-monitoring--incident-response) |
| 42 | **Update `OpenAPI.md` §11 YAML `required` list** | `standards_used`, `license_type`, `deidentification_method`, `access_control_method` are required in code but missing from YAML's `required:` array at line 1276. | Cross-ref [`OpenAPI.md §11`](./OpenAPI.md#11-yaml-specification) vs code |
| 43 | **Update `SECURITY_AUDIT_CHECKLIST.md`** | Mark done items: SecurityHeadersMiddleware ✅, password validator ✅, docs disabled in prod ✅, JWT HS256 ✅, frontend non-root user ✅, autoescape ✅, no dangerouslySetInnerHTML ✅, no localStorage ✅, no eval ✅ | Current state audit |

---

## 7. Database Hardening (5 items)

Source: [`SEC.md §7.1`](./SECURITY_AUDIT_CHECKLIST.md#71-postgresql-ref-tdd-6-ddl).

| # | Item | Details |
|---|---|---|
| 44 | **Separate DB roles** | Create `toolkit_api` (SELECT/INSERT on assessment tables), `toolkit_worker` (INSERT on results), `toolkit_readonly` — currently single user |
| 45 | **scram-sha-256** | Enable `password_encryption = 'scram-sha-256'` in postgresql.conf |
| 46 | **Row-Level Security** | Enable RLS on `assessments` table with `assessment_owner_policy` (defense-in-depth) |
| 47 | **Connection limits** | `ALTER ROLE toolkit_api CONNECTION LIMIT 20`, worker 10 |
| 48 | **SSL enforcement** | Enable `ssl = on` in postgresql.conf; `hostssl` in pg_hba.conf |

---

## 8. Webhook & Worker (3 items)

| # | Item | Details | Source |
|---|---|---|---|
| 49 | **Webhook retry alignment** | Code: `max_retries=5` with backoff `2^n * 30` (30/60/120/240/480s). OpenAPI §8: 3 retries at 30/120/480s. Align both directions. | Cross-ref `backend/app/worker/tasks.py:64,450,485` vs [`OpenAPI.md §8`](./OpenAPI.md#8-webhook-contract-aikosh-inbound) |
| 50 | **Webhook HMAC signature** | Add `X-Toolkit-Signature` header (HMAC-SHA256 of payload body) in addition to Bearer token. | [`SEC.md §1.10 item 163`](./SECURITY_AUDIT_CHECKLIST.md#110-integration-aikosh-webhook--backendappintegrationaikosh_webhookpy) |
| 51 | **Flower auth in docker-compose** | Add `--basic_auth=admin:${FLOWER_PASSWORD}` to Flower command (currently runs with no auth). | [`SEC.md §1.6 item 115`](./SECURITY_AUDIT_CHECKLIST.md#16-message-broker-redis-72--backendappworkercelery_apppy) |

---

## Summary

| Category | Count |
|---|---|
| Security test files | 14 |
| Infrastructure hardening | 14 |
| CI/CD pipeline | 4 |
| Schema/validation enhancements | 5 |
| Security headers/middleware | 2 |
| Documentation | 4 |
| Database hardening | 5 |
| Webhook & worker | 3 |
| **Total** | **51** |

**Already verified clean (no action needed):**
- Frontend static analysis: no `dangerouslySetInnerHTML`, no `localStorage`/`sessionStorage`, no `eval()`, `credentials: 'include'` present, Zustand `persist` not used
- Frontend Dockerfile: already has non-root `USER nextjs`
- JWT algorithm: restricted to `HS256` explicitly
- Swagger docs: disabled when `ENVIRONMENT=production`
- Password validator: regex enforced server-side in `auth.py`
- Report autoescape: `autoescape=select_autoescape(["html", "xml"])` in `generator.py`
- SecurityHeadersMiddleware: X-Content-Type-Options, X-Frame-Options, HSTS all present
