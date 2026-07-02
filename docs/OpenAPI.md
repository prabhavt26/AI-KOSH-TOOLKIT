> **Product Goal:** A user-facing, browser-first web application for automated MIDAS-grade health dataset quality assessment — with a secure multi-tenant backend, async processing pipeline, and a REST API surface that external platforms (AIKosh) can integrate with programmatically.

# OpenAPI Specification
# AIKosh Dataset Quality Evaluation Toolkit

---

**Document Version:** 1.1  
**Status:** Active  
**Last Updated:** June 24, 2026  
**Prepared For:** AIKosh / IndiaAI Mission  
**References:** PRD v1.1, TDD v1.1  
**Classification:** Internal Working Document

---

> This document is the human-readable form of the API contract.  
> The machine-readable `.yaml` file is generated directly from this specification.  
> Every field, type, constraint, and example here is authoritative — frontend, backend, and AIKosh integration teams all build against this.

---

## Table of Contents

1. [API Overview](#1-api-overview)
2. [Base URL & Versioning](#2-base-url--versioning)
3. [Authentication](#3-authentication)
4. [Common Conventions](#4-common-conventions)
5. [Rate Limiting](#5-rate-limiting)
6. [Schemas (Data Models)](#6-schemas-data-models)
   - 6.1 MetadataForm
   - 6.2 AssessmentSubmitResponse
   - 6.3 AssessmentStatusResponse
   - 6.4 AssessmentResultResponse
   - 6.5 DomainScoreObject
   - 6.6 CQIResult
   - 6.7 PRSResult
   - 6.8 ReleaseClassification
   - 6.9 ReportURLs
   - 6.10 AuditLogResponse
   - 6.11 AuditEvent
   - 6.12 AssessmentListItem
   - 6.13 HealthResponse
   - 6.14 ErrorResponse
7. [Endpoints](#7-endpoints)
   - 7.1 POST /api/v1/assess
   - 7.2 GET /api/v1/assess/{assessment_id}
   - 7.3 GET /api/v1/assess/{assessment_id}/report
   - 7.4 GET /api/v1/assess/{assessment_id}/audit
   - 7.5 GET /api/v1/datasets/{dataset_id}/assessments
   - 7.6 GET /api/v1/health
8. [Webhook Contract (AIKosh Inbound)](#8-webhook-contract-aikosh-inbound)
9. [Error Reference](#9-error-reference)
10. [Enum Reference](#10-enum-reference)
11. [YAML Specification](#11-yaml-specification)

---

## 1. API Overview

The AIKosh Dataset Quality Evaluation Toolkit exposes a REST API that enables:

- **Web UI users** to register, login, upload datasets, monitor assessment progress, view quality results, and download reports through a browser interface
- **Dataset custodians** (via API key) to submit health research datasets programmatically for automated MIDAS-inspired quality assessment
- **AIKosh platform** to trigger assessments on dataset submission and receive quality metadata via webhook
- **Reviewers** to retrieve assessment results, reports, and audit logs (administrators manage user states but cannot access dataset results or reports due to privacy boundaries)

The API is asynchronous. Submitting a dataset returns an `assessment_id` immediately. The client either polls the status endpoint or waits for a webhook callback. Processing time is typically under 3 minutes for datasets up to 1GB.

**Dataset files are uploaded directly to AWS S3 via temporary pre-signed URLs. All other request and response bodies are JSON.**

---

## 2. Base URL & Versioning

| Environment | Base URL |
|---|---|
| Production | `https://toolkit.aikosh.gov.in` |
| Staging | `https://toolkit-staging.aikosh.gov.in` |
| Development (local) | `http://localhost:8000` |

All endpoints are prefixed with `/api/v1/`. The version is part of the URL path, not a header.

---

## 3. Authentication

The system uses a **Dual-Authentication Model** to support both secure human browser interactions and programmatic machine integrations.

### 3.1 User Session Authentication (Browser UI)
- **Mechanism:** JWT stored in a secure, `HttpOnly`, `Secure`, `SameSite=Lax` cookie named `session_token`.
- **Session Duration:** Persistent session cookies that remain signed in until cleared.
- **Onboarding:** Instantly activated and logged in upon sign-up.

### 3.2 Developer API Key Authentication (Machine Integrations)
- **Mechanism:** API key passed as a Bearer token in the `Authorization` header.
  ```
  Authorization: Bearer <api_key>
  ```
- **Key format:** `tkt_live_{32 alphanumeric characters}`.
- **Storage:** Stored in the database as SHA-256 hashes for cryptographic safety.

### 3.3 Roles & Access Boundaries

| Role | Permissions & Boundaries |
|---|---|
| `user` (submitter) | Submit assessments, view results, download reports (limited to own datasets only). |
| `reviewer` | All user permissions + view audit logs. |
| `admin` | View/manage users list (activate/suspend). Admins **cannot** download user datasets or view user reports. |

**Auth errors:**

| Condition | HTTP Status | Error Code |
|---|---|---|
| Missing session cookie and auth header | 401 | `missing_credentials` |
| Invalid or expired token/key | 401 | `invalid_credentials` |
| Insufficient role permissions | 403 | `insufficient_permissions` |

---

## 4. Common Conventions

### Request IDs
Every response includes an `X-Request-ID` header (UUID) for tracing. Include this in support queries.

### Timestamps
All timestamps are ISO 8601 in UTC: `2026-06-18T10:34:22Z`

### UUIDs
All IDs (`assessment_id`, `result_id`, `log_id`) are UUID v4: `a3f7c2d1-9b4e-4f2a-bc31-7d8e9f1a2b3c`

### Pagination
List endpoints use `limit` + `offset` pagination:
- `limit`: max records to return (default: 10, max: 50)
- `offset`: number of records to skip (default: 0)
- Response includes `total`, `limit`, `offset` fields

### Null vs Absent
- A field with value `null` means the field exists but has no value (e.g. Domain 11 score when not applicable)
- An absent field means it is not relevant to this response shape
- Never assume absent = null

---

## 5. Rate Limiting

| Limit | Value |
|---|---|
| Requests per minute per API key | 100 |
| Concurrent active assessments per API key | 10 |
| Max file size per submission | 5 GB |

**Rate limit headers returned on every response:**

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1718706000
```

When rate limit is exceeded: HTTP 429 with error code `rate_limit_exceeded`.

---

## 6. Schemas (Data Models)

---

### 6.1 MetadataForm

Submitted inside the JSON request body under the key "metadata" in `POST /api/v1/assess`.

| Field | Type | Required | Description |
|---|---|---|---|
| `dataset_name` | string | ✅ | Name of the dataset |
| `dataset_version` | string | ❌ | Version string, e.g. `"1.0.0"` or `"v2"` |
| `dataset_type` | string (enum) | ✅ | `tabular` \| `imaging` \| `text` \| `multimodal` |
| `study_type` | string (enum) | ✅ | `RCT` \| `cohort` \| `cross_sectional` \| `registry` \| `observational` \| `case_control` \| `other` |
| `target_population` | string | ✅ | Description of the study population |
| `geographic_coverage` | string (enum) | ✅ | `village` \| `taluk` \| `district` \| `state` \| `national` \| `multi_country` |
| `age_range_min` | integer | ❌ | Minimum age in study population (years) |
| `age_range_max` | integer | ❌ | Maximum age in study population (years) |
| `sex_distribution` | string (enum) | ❌ | `male_only` \| `female_only` \| `both` \| `not_specified` |
| `num_sites` | integer | ❌ | Number of data collection sites |
| `collection_start_date` | string (date) | ❌ | Format: `YYYY-MM-DD` |
| `collection_end_date` | string (date) | ❌ | Format: `YYYY-MM-DD` |
| `annotation_methodology` | string | ❌ | Description of annotation process (if applicable) |
| `num_annotators` | integer | ❌ | Number of annotators used |
| `irr_method` | string | ❌ | Inter-rater reliability method, e.g. `"Cohen's Kappa"` |
| `irr_value` | number | ❌ | IRR metric value, e.g. `0.82` |
| `standards_used` | string | ✅ | e.g. `"FHIR R4"`, `"ICD-10"`, `"SNOMED CT"`, `"custom"` |
| `ethics_approval_ref` | string | ❌ | Ethics committee reference number |
| `consent_type` | string (enum) | ✅ | `individual` \| `waiver` \| `community` \| `not_applicable` |
| `deidentification_method` | string | ✅ | Description of de-identification applied |
| `differential_privacy_applied` | boolean | ❌ | Whether Differential Privacy was applied (default: `false`) |
| `dp_epsilon` | number | ❌ | DP epsilon value if `differential_privacy_applied` is `true`. Must be > 0 |
| `sensitivity_class` | string (enum) | ✅ | `standard` \| `high_stigma` \| `critical` |
| `persistent_identifier` | string | ❌ | DOI or accession number, e.g. `"10.5281/zenodo.1234567"` |
| `license_type` | string | ✅ | e.g. `"CC BY 4.0"`, `"CC BY-NC 4.0"`, `"restricted"` |
| `synthetic_data_pct` | number | ❌ | Percentage of synthetic data in dataset (0–100). `0` or absent = Domain 11 N/A |
| `annotator_qualifications` | string (enum) | ❌ | `clinician` \| `student` \| `crowdsourced` \| `automated` \| `mixed` \| `other` |
| `dq_checks_applied` | array of strings | ❌ | List of automated DQ checks applied |
| `direct_identifiers_present` | array of strings | ❌ | List of direct identifiers declared present |
| `k_anonymity_value` | integer | ❌ | Measured k-anonymity value |
| `location_granularity` | string (enum) | ❌ | `village` \| `taluk` \| `district` \| `state` \| `national` \| `multi_country` \| `none` |
| `temporal_granularity` | string (enum) | ❌ | `day` \| `month` \| `year` \| `not_applicable` |
| `rare_condition_flag` | boolean | ❌ | Whether dataset contains rare medical conditions |
| `synthetic_utility_evaluated` | boolean | ❌ | Utility evaluation status for synthetic data |
| `synthetic_privacy_tested` | boolean | ❌ | Empirical privacy testing status for synthetic data |
| `equity_analysis_performed` | boolean | ❌ | Equity & demographic fairness analysis status |
| `community_engagement` | boolean | ❌ | Indigenous/community governance engagement |
| `redressal_mechanism_exists` | boolean | ❌ | Grievance redressal mechanism status |
| `dua_required` | boolean | ❌ | Data use agreement requirement status |
| `named_steward_exists` | boolean | ❌ | Named data steward assignment status |
| `dpdp_compliance_status` | string (enum) | ❌ | `fully_compliant` \| `partially_compliant` \| `not_compliant` \| `not_applicable` |
| `access_control_method` | string | ✅ | Description of access controls in place |
| `linked_model_ids` | array of strings | ❌ | AIKosh or HuggingFace model IDs linked to this dataset |
| `data_dictionary_uploaded` | boolean | ❌ | Whether a data dictionary was uploaded as an attachment (default: `false`) |
| `provenance_pipeline_available` | boolean | ❌ | Whether a pipeline script was uploaded (default: `false`) |
| `github_repo_url` | string (url) | ❌ | GitHub/GitLab repository URL for the dataset pipeline |
| `changelog_provided` | boolean | ❌ | Whether a changelog was provided (default: `false`) |
| `version_format` | string (enum) | ❌ | `semantic` \| `arbitrary` \| `none` |
| `sustainability_info_provided` | boolean | ❌ | Whether energy/carbon footprint information was provided |
| `feedback_mechanism_exists` | boolean | ❌ | Whether a user feedback channel exists for the dataset |
| `aikosh_dataset_id` | string | ❌ | AIKosh platform dataset ID (if already registered on AIKosh) |
| `webhook_url` | string (url) | ❌ | Override webhook URL for this specific submission |

**Validation rules:**
- `dp_epsilon` is required if `differential_privacy_applied` is `true`
- `dp_epsilon` must be > 0 if provided
- `synthetic_data_pct` must be between 0 and 100
- `irr_value` must be between 0 and 1
- `num_annotators` must be ≥ 1 if provided
- `collection_end_date` must be ≥ `collection_start_date` if both provided
- `age_range_max` must be ≥ `age_range_min` if both provided
- Neither `collection_start_date` nor `collection_end_date` can be a future date

**Example:**
```json
{
  "dataset_name": "Multi-site TB Cohort Study India 2019–2023",
  "dataset_version": "1.0.0",
  "dataset_type": "tabular",
  "study_type": "cohort",
  "target_population": "Adults with confirmed pulmonary TB across 14 RNTCP sites",
  "geographic_coverage": "state",
  "age_range_min": 18,
  "age_range_max": 75,
  "sex_distribution": "both",
  "num_sites": 14,
  "collection_start_date": "2019-01-01",
  "collection_end_date": "2023-12-31",
  "standards_used": "ICD-10",
  "ethics_approval_ref": "ICMR/IEC/2018/0042",
  "consent_type": "individual",
  "deidentification_method": "HIPAA Safe Harbor — all 18 identifiers removed",
  "differential_privacy_applied": false,
  "sensitivity_class": "high_stigma",
  "persistent_identifier": "10.5281/zenodo.9876543",
  "license_type": "CC BY-NC 4.0",
  "synthetic_data_pct": 0,
  "access_control_method": "DUA required; access via AIKosh controlled release",
  "data_dictionary_uploaded": true,
  "provenance_pipeline_available": false,
  "changelog_provided": false,
  "version_format": "semantic",
  "sustainability_info_provided": false,
  "feedback_mechanism_exists": false,
  "aikosh_dataset_id": "aikosh-hrd-00421"
}
```

---

### 6.2 AssessmentSubmitResponse

Returned immediately on `POST /api/v1/assess` (HTTP 202 Accepted).

| Field | Type | Description |
|---|---|---|
| `assessment_id` | string (UUID) | Unique ID for this assessment — use for all subsequent calls |
| `status` | string | Always `"queued"` at this point |
| `estimated_completion_seconds` | integer | Estimated processing time in seconds |
| `poll_url` | string | Full URL to poll for status/results |
| `submitted_at` | string (datetime) | When the assessment was queued |

**Example:**
```json
{
  "assessment_id": "a3f7c2d1-9b4e-4f2a-bc31-7d8e9f1a2b3c",
  "status": "queued",
  "estimated_completion_seconds": 180,
  "poll_url": "/api/v1/assess/a3f7c2d1-9b4e-4f2a-bc31-7d8e9f1a2b3c",
  "submitted_at": "2026-06-18T10:30:00Z"
}
```

---

### 6.3 AssessmentStatusResponse

Returned by `GET /api/v1/assess/{assessment_id}` when the assessment is still in progress or failed.

| Field | Type | Description |
|---|---|---|
| `assessment_id` | string (UUID) | Assessment ID |
| `status` | string (enum) | `queued` \| `processing` \| `complete` \| `failed` |
| `dataset_id` | string | AIKosh dataset ID (if provided in submission) |
| `submitted_at` | string (datetime) | Submission timestamp |
| `started_at` | string (datetime) \| null | When Celery worker began processing |
| `completed_at` | string (datetime) \| null | When processing completed (null if still running) |
| `error_message` | string \| null | Populated only when `status` is `"failed"` |
| `error_traceback` | string \| null | Full stack trace populated only when `status` is `"failed"` |

**Example (processing):**
```json
{
  "assessment_id": "a3f7c2d1-9b4e-4f2a-bc31-7d8e9f1a2b3c",
  "status": "processing",
  "dataset_id": "aikosh-hrd-00421",
  "submitted_at": "2026-06-18T10:30:00Z",
  "started_at": "2026-06-18T10:30:04Z",
  "completed_at": null,
  "error_message": null,
  "error_traceback": null
}
```

**Example (failed):**
```json
{
  "assessment_id": "a3f7c2d1-9b4e-4f2a-bc31-7d8e9f1a2b3c",
  "status": "failed",
  "dataset_id": "aikosh-hrd-00421",
  "submitted_at": "2026-06-18T10:30:00Z",
  "started_at": "2026-06-18T10:30:04Z",
  "completed_at": "2026-06-18T10:31:12Z",
  "error_message": "Profiling failed: file encoding could not be determined",
  "error_traceback": "Traceback (most recent call last):\n  File \"app/worker/tasks.py\", line 45, in run_profile\n    profile = profile_dataset(file_path)\n  File \"app/profiler/engine.py\", line 12, in profile_dataset\n    raise ValueError(\"file encoding could not be determined\")\nValueError: file encoding could not be determined"
}
```

---

### 6.4 AssessmentResultResponse

Returned by `GET /api/v1/assess/{assessment_id}` when `status` is `"complete"`. This is the full result payload.

| Field | Type | Description |
|---|---|---|
| `assessment_id` | string (UUID) | Assessment ID |
| `status` | string | `"complete"` |
| `dataset_id` | string \| null | AIKosh dataset ID |
| `dataset_name` | string | Dataset name from metadata form |
| `toolkit_version` | string | Version of toolkit that produced this assessment |
| `assessed_at` | string (datetime) | When assessment completed |
| `domain_11_applicable` | boolean | Whether Domain 11 was included in CQI calculation |
| `cqi` | CQIResult object | Full CQI computation result |
| `prs` | PRSResult object | Full PRS computation result |
| `release` | ReleaseClassification object | Release classification with justification |
| `domain_scores` | array of DomainScoreObject | All 15 domain scores |
| `profile_summary` | object | Key facts from dataset profiling |
| `report_urls` | ReportURLs object | Pre-signed URLs for JSON/HTML/PDF reports |
| `audit_log_id` | string (UUID) | Reference to audit log for this assessment |

**`profile_summary` object:**

| Field | Type | Description |
|---|---|---|
| `rows` | integer | Number of rows in dataset |
| `columns` | integer | Number of columns |
| `file_format` | string | Detected file format |
| `file_size_bytes` | integer | File size |
| `overall_completeness_pct` | number | Overall column completeness % |
| `direct_identifiers_detected` | boolean | Whether PII was detected |
| `icd_codes_detected` | boolean | Whether ICD codes were found |
| `sampled` | boolean | Whether profiling used sampling (large files) |
| `sample_rows` | integer \| null | Number of rows sampled (null if full scan) |

**Example:**
```json
{
  "assessment_id": "a3f7c2d1-9b4e-4f2a-bc31-7d8e9f1a2b3c",
  "status": "complete",
  "dataset_id": "aikosh-hrd-00421",
  "dataset_name": "Multi-site TB Cohort Study India 2019–2023",
  "toolkit_version": "1.0.0",
  "assessed_at": "2026-06-18T10:34:22Z",
  "domain_11_applicable": false,
  "cqi": {
    "value": 67.9,
    "band": "Silver",
    "total_score": 38,
    "max_possible": 56,
    "formula_trace": "(38 / 56) × 100 = 67.9"
  },
  "prs": {
    "value": 22,
    "band": "Moderate",
    "baseline_risk": 15.0,
    "sensitivity_class": "high_stigma",
    "sensitivity_multiplier": 1.5,
    "adjusted_risk": 22.5,
    "computation_trace": "baseline=15.0 × multiplier=1.5 = 22.5 → PRS=22",
    "differential_privacy_applied": false,
    "epsilon": null
  },
  "release": {
    "classification": "Controlled",
    "justification": "TB dataset — high-stigma data defaults to Controlled regardless of PRS band.",
    "policy_override_applied": true
  },
  "domain_scores": [ ... ],
  "profile_summary": {
    "rows": 12450,
    "columns": 38,
    "file_format": "csv",
    "file_size_bytes": 45231890,
    "overall_completeness_pct": 94.2,
    "direct_identifiers_detected": false,
    "icd_codes_detected": true,
    "sampled": false,
    "sample_rows": null
  },
  "report_urls": {
    "json": "https://s3.ap-south-1.amazonaws.com/aikosh-toolkit/reports/a3f7.../report.json?X-Amz-Expires=86400&...",
    "html": "https://s3.ap-south-1.amazonaws.com/aikosh-toolkit/reports/a3f7.../report.html?X-Amz-Expires=86400&...",
    "pdf": "https://s3.ap-south-1.amazonaws.com/aikosh-toolkit/reports/a3f7.../report.pdf?X-Amz-Expires=86400&..."
  },
  "audit_log_id": "b7e2a1f3-4c9d-4e0b-8a2c-1d7f3e8b9c0a"
}
```

---

### 6.5 DomainScoreObject

One object per domain. The `domain_scores` array in `AssessmentResultResponse` contains 15 of these.

| Field | Type | Description |
|---|---|---|
| `domain_number` | integer | 1–15 |
| `domain_name` | string | Full domain name (e.g. `"Annotation / Labelling Reliability"`) |
| `score` | integer \| null | 0–4. `null` if `not_applicable` is `true` |
| `max_score` | integer \| null | Always 4. `null` if `not_applicable` is `true` |
| `not_applicable` | boolean | `true` only for Domain 11 when no synthetic data |
| `confidence` | string (enum) \| null | `"High"` \| `"Medium"` \| `"Low"` |
| `rationale` | string \| null | One-sentence explanation of the score |
| `evidence_items` | array of strings | What was found that supported this score |
| `gaps` | array of strings | What was missing that prevented a higher score |
| `inferred` | boolean | `true` if scoring criteria were inferred, not directly from public MIDAS docs |

**Example (Domain 5 — Data Structure & Interoperability):**
```json
{
  "domain_number": 5,
  "domain_name": "Data Structure & Interoperability",
  "score": 3,
  "max_score": 4,
  "not_applicable": false,
  "confidence": "High",
  "rationale": "ICD-10 codes detected in diagnosis columns. Column completeness 94.2% meets ≥90% threshold.",
  "evidence_items": [
    "ICD-10 code pattern detected in column: diagnosis_icd10 (n=12,430 valid codes)",
    "Overall column completeness: 94.2%",
    "No value range violations detected in numeric columns",
    "Standard declared in metadata: ICD-10"
  ],
  "gaps": [
    "Machine-readable data dictionary aligned to ontology not provided — required for Score 4",
    "Referential integrity check across related columns: 3 violations detected in site_id references"
  ],
  "inferred": false
}
```

**Example (Domain 11 — N/A):**
```json
{
  "domain_number": 11,
  "domain_name": "Synthetic / Simulated Data",
  "score": null,
  "max_score": null,
  "not_applicable": true,
  "confidence": null,
  "rationale": "Dataset contains no synthetic or simulated data. Domain excluded from CQI calculation.",
  "evidence_items": [],
  "gaps": [],
  "inferred": false
}
```

---

### 6.6 CQIResult

| Field | Type | Description |
|---|---|---|
| `value` | number | CQI score (0–100, 1 decimal place) |
| `band` | string (enum) | `"Diamond"` \| `"Platinum"` \| `"Gold"` \| `"Silver"` \| `"Bronze"` \| `"Remediation"` |
| `total_score` | integer | Sum of all applicable domain scores |
| `max_possible` | integer | 60 (if Domain 11 applicable) or 56 (if not) |
| `formula_trace` | string | Human-readable formula, e.g. `"(38 / 56) × 100 = 67.9"` |

---

### 6.7 PRSResult

| Field | Type | Description |
|---|---|---|
| `value` | integer | PRS score (0–100, integer) |
| `band` | string (enum) | `"Low"` \| `"Moderate"` \| `"High"` \| `"Very High"` |
| `baseline_risk` | number | Step 1 identification risk before sensitivity adjustment |
| `sensitivity_class` | string (enum) | `"standard"` \| `"high_stigma"` \| `"critical"` |
| `sensitivity_multiplier` | number | 1.0, 1.5, or 2.0 |
| `adjusted_risk` | number | `baseline_risk × sensitivity_multiplier` before rounding |
| `computation_trace` | string | Full trace of PRS computation |
| `differential_privacy_applied` | boolean | Whether DP was used in baseline risk computation |
| `epsilon` | number \| null | DP epsilon value if `differential_privacy_applied` is `true` |

---

### 6.8 ReleaseClassification

| Field | Type | Description |
|---|---|---|
| `classification` | string (enum) | `"Open"` \| `"Controlled"` \| `"Restricted"` |
| `justification` | string | Human-readable reason for the classification |
| `policy_override_applied` | boolean | `true` if high-stigma/critical override was applied rather than standard matrix |

---

### 6.9 ReportURLs

| Field | Type | Description |
|---|---|---|
| `json` | string (url) | Pre-signed URL for JSON report (24-hour expiry) |
| `html` | string (url) | Pre-signed URL for HTML report (24-hour expiry) |
| `pdf` | string (url) | Pre-signed URL for PDF report (24-hour expiry) |

---

### 6.10 AuditLogResponse

Returned by `GET /api/v1/assess/{assessment_id}/audit`.

| Field | Type | Description |
|---|---|---|
| `assessment_id` | string (UUID) | Assessment ID |
| `total_events` | integer | Total number of audit events |
| `events` | array of AuditEvent | Ordered by `event_timestamp` ascending |

---

### 6.11 AuditEvent

| Field | Type | Description |
|---|---|---|
| `log_id` | string (UUID) | Unique audit event ID |
| `event_type` | string | Event type (see Enum Reference §10 for full list) |
| `event_timestamp` | string (datetime) | When the event occurred |
| `component` | string \| null | Which system component fired this event |
| `event_detail` | object | Arbitrary structured detail specific to this event type |
| `severity` | string (enum) | `"INFO"` \| `"WARNING"` \| `"ERROR"` |

**Example:**
```json
{
  "log_id": "c1d2e3f4-5a6b-7c8d-9e0f-1a2b3c4d5e6f",
  "event_type": "domain_7_scored",
  "event_timestamp": "2026-06-18T10:33:12Z",
  "component": "domain_07_privacy",
  "event_detail": {
    "score": 4,
    "confidence": "High",
    "direct_identifiers_detected": false,
    "deidentification_method": "HIPAA Safe Harbor"
  },
  "severity": "INFO"
}
```

---

### 6.12 AssessmentListItem

One item in the paginated list returned by `GET /api/v1/datasets/{dataset_id}/assessments`.

| Field | Type | Description |
|---|---|---|
| `assessment_id` | string (UUID) | Assessment ID |
| `status` | string (enum) | `queued` \| `processing` \| `complete` \| `failed` |
| `submitted_at` | string (datetime) | Submission timestamp |
| `completed_at` | string (datetime) \| null | Completion timestamp |
| `cqi` | number \| null | CQI value (null if not yet complete) |
| `cqi_band` | string \| null | CQI band (null if not yet complete) |
| `prs` | integer \| null | PRS value (null if not yet complete) |
| `release_classification` | string \| null | Release class (null if not yet complete) |
| `toolkit_version` | string | Toolkit version used |

---

### 6.13 HealthResponse

| Field | Type | Description |
|---|---|---|
| `status` | string | `"healthy"` \| `"degraded"` \| `"unhealthy"` |
| `version` | string | Toolkit version |
| `timestamp` | string (datetime) | Current server time |
| `dependencies` | object | Status of each dependency |

**`dependencies` object:**

| Field | Type | Description |
|---|---|---|
| `postgres` | string | `"ok"` \| `"error"` |
| `redis` | string | `"ok"` \| `"error"` |
| `s3` | string | `"ok"` \| `"error"` |
| `celery_workers` | string | `"ok"` \| `"no_workers"` \| `"error"` |

**Example:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-06-18T10:00:00Z",
  "dependencies": {
    "postgres": "ok",
    "redis": "ok",
    "s3": "ok",
    "celery_workers": "ok"
  }
}
```

---

### 6.14 ErrorResponse

All error responses use this structure.

| Field | Type | Description |
|---|---|---|
| `error` | string | Machine-readable error code (see §9) |
| `message` | string | Human-readable description |
| `detail` | object \| null | Additional context (field-level validation errors, etc.) |
| `request_id` | string (UUID) | Request ID for tracing |

**Example:**
```json
{
  "error": "validation_error",
  "message": "Metadata form validation failed",
  "detail": {
    "dp_epsilon": "Required when differential_privacy_applied is true",
    "sensitivity_class": "Must be one of: standard, high_stigma, critical"
  },
  "request_id": "f1a2b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c"
}
```

---

## 7. Endpoints

### 7.0 Authentication & Admin Endpoints

#### POST /api/v1/auth/register
**Register a new user account.**
- **Onboarding Behavior:** Upon registration, the user account is instantly activated and logged in. The backend automatically sets the secure `session_token` cookie so the user does not need a separate activation/login step.
- **Auth:** Not required
- **Content-Type:** `application/json`
- **Request Body:**
  ```json
  {
    "email": "user@example.com",
    "password": "secure_password"
  }
  ```
- **Response (HTTP 201 Created):** Sets `session_token` cookie and returns:
  ```json
  {
    "user_id": "a3f7c2d1-9b4e-4f2a-bc31-7d8e9f1a2b3c",
    "email": "user@example.com"
  }
  ```

#### POST /api/v1/auth/login
**Login and receive session token cookie.**
- **Auth:** Not required
- **Content-Type:** `application/json`
- **Request Body:** Same as register.
- **Response (HTTP 200 OK):** Sets `session_token` cookie.
  ```json
  {
    "message": "Login successful"
  }
  ```

#### POST /api/v1/auth/logout
**Log out and clear session cookie.**
- **Auth:** Required (valid session)
- **Response (HTTP 200 OK):**
  ```json
  {
    "message": "Logged out successfully"
  }
  ```

#### GET /api/v1/auth/keys
**List all active developer API keys for the current user.**
- **Auth:** Required (session cookie only)
- **Response (HTTP 200 OK):**
  ```json
  {
    "keys": [
      {
        "key_id": "b4e8c9d1-0f3a-4e2b-9c31-8d9e0f1a2b3c",
        "key_prefix": "tkt_live_ab12",
        "created_at": "2026-06-18T10:30:00Z",
        "last_used_at": "2026-06-18T11:45:00Z",
        "expires_at": null
      }
    ]
  }
  ```

#### POST /api/v1/auth/keys
**Generate a new database-backed developer API key.**
- **Auth:** Required (session cookie only)
- **Response (HTTP 201 Created):** Returns the raw key (only visible once) and key metadata.
  ```json
  {
    "key_id": "b4e8c9d1-0f3a-4e2b-9c31-8d9e0f1a2b3c",
    "key_prefix": "tkt_live_ab12",
    "raw_key": "tkt_live_ab12cd34ef56gh78ij90kl12mn34op56",
    "created_at": "2026-06-18T10:30:00Z",
    "expires_at": null
  }
  ```

#### DELETE /api/v1/auth/keys/{key_id}
**Revoke / delete a developer API key.**
- **Auth:** Required (session cookie only)
- **Response (HTTP 200 OK):**
  ```json
  {
    "message": "API key revoked successfully"
  }
  ```

#### GET /api/v1/admin/users
**List all registered users (Admin only).**
- **Auth:** Required (role `admin`)
- **Response (HTTP 200 OK):**
  ```json
  {
    "users": [
      {
        "user_id": "a3f7c2d1-9b4e-4f2a-bc31-7d8e9f1a2b3c",
        "email": "user@example.com",
        "role": "user",
        "is_active": true,
        "created_at": "2026-06-18T10:30:00Z"
      }
    ]
  }
  ```

#### POST /api/v1/admin/users/{user_id}/toggle-active
**Suspend or reactivate user account (Admin only).**
- **Auth:** Required (role `admin`)
- **Response (HTTP 200 OK):**
  ```json
  {
    "user_id": "a3f7c2d1-9b4e-4f2a-bc31-7d8e9f1a2b3c",
    "is_active": false
  }
  ```

### 7.1 POST /api/v1/assess/upload-url

**Request a temporary pre-signed AWS S3 upload URL.**
- **Auth:** Required (session cookie or Bearer API key)
- **Content-Type:** `application/json`
- **Request Body:**
  ```json
  {
    "filename": "tb_cohort_2023.csv",
    "file_format": "csv"
  }
  ```
- **Response (HTTP 200 OK):**
  ```json
  {
    "upload_url": "http://localhost:9000/aikosh-datasets/uploads/a3f7c2d1-9b4e-4f2a-bc31-7d8e9f1a2b3c/dataset.csv?X-Amz-Signature=...",
    "file_key": "uploads/a3f7c2d1-9b4e-4f2a-bc31-7d8e9f1a2b3c/dataset.csv",
    "assessment_id": "a3f7c2d1-9b4e-4f2a-bc31-7d8e9f1a2b3c"
  }
  ```

---

### 7.2 POST /api/v1/assess

**Submit dataset metadata and S3 file key for quality assessment.**
- **Auth:** Required (session cookie or Bearer API key)
- **Content-Type:** `application/json`

#### Request Body (JSON)
```json
{
  "file_key": "uploads/a3f7c2d1-9b4e-4f2a-bc31-7d8e9f1a2b3c/dataset.csv",
  "metadata": {
    "dataset_name": "Multi-site TB Cohort Study India 2019–2023",
    "dataset_version": "1.0.0",
    "dataset_type": "tabular",
    "study_type": "cohort",
    "target_population": "Adults with pulmonary TB",
    "geographic_coverage": "state",
    "sensitivity_class": "high_stigma"
  },
  "data_dictionary_key": "uploads/a3f7c2d1-9b4e-4f2a-bc31-7d8e9f1a2b3c/data_dictionary.pdf",
  "sop_key": null,
  "consent_doc_key": null,
  "pipeline_script_key": null
}
```

#### Response

**202 Accepted** — Assessment queued. Returns `AssessmentSubmitResponse`.

```json
{
  "assessment_id": "a3f7c2d1-9b4e-4f2a-bc31-7d8e9f1a2b3c",
  "status": "queued",
  "estimated_completion_seconds": 180,
  "poll_url": "/api/v1/assess/a3f7c2d1-9b4e-4f2a-bc31-7d8e9f1a2b3c",
  "submitted_at": "2026-06-18T10:30:00Z"
}
```

#### Error Responses

| HTTP Status | Error Code | When |
|---|---|---|
| 400 | `missing_file_key` | No `file_key` in request body |
| 400 | `missing_metadata` | No `metadata` in request body |
| 404 | `file_not_found_in_s3` | Key does not exist in AWS S3 |
| 422 | `unsupported_format` | File key extension/type is not accepted |
| 422 | `validation_error` | Metadata fails schema validation |
| 429 | `rate_limit_exceeded` | Too many requests |

> [!IMPORTANT]
> **Implementation Note — Upload Flow Mismatch:**
> The documented flow above (pre-signed URL → upload to S3 → POST with `file_key`) is the **target design** specified in this contract.
> The current backend implementation (`backend/app/api/v1/assess.py`) accepts `multipart/form-data` with the file attached directly.
> The pre-signed URL endpoint (`POST /api/v1/assess/upload-url`) is **not yet implemented**.
> Migration to this two-step pre-signed URL flow is required before the first production deployment.
> Until then, the actual submission endpoint accepts: `Content-Type: multipart/form-data` with fields `file` (binary) and `metadata` (JSON string).

- `estimated_completion_seconds` is a rough estimate based on file size and current queue depth. Do not use as a hard guarantee.
- The `data_dictionary`, `sop`, `consent_doc`, and `pipeline_script` attachments directly affect Domain 1, 3, 9, and 10 scoring. Submitting them improves score accuracy.
- The `metadata` field must be a valid JSON string, not a file.

---

### 7.2 GET /api/v1/assess/{assessment_id}

**Get assessment status or full results.**

**Auth:** Required (any role)  
**Path parameter:** `assessment_id` — UUID of the assessment

#### Response

Returns different response shapes depending on `status`:

| Status | HTTP Code | Response Schema |
|---|---|---|
| `queued` or `processing` | 200 | `AssessmentStatusResponse` |
| `complete` | 200 | `AssessmentResultResponse` |
| `failed` | 200 | `AssessmentStatusResponse` (with `error_message` populated) |
| Not found | 404 | `ErrorResponse` |
| Belongs to different API key | 403 | `ErrorResponse` |

#### Polling Guidance
- Poll at 10-second intervals for the first 60 seconds
- Then poll every 30 seconds until complete or failed
- Assessment never remains in `processing` for more than 6 minutes before transitioning to `failed`

#### Example — Complete Response

See §6.4 for the full `AssessmentResultResponse` example.

---

### 7.3 GET /api/v1/assess/{assessment_id}/report

**Download the quality assessment report.**

**Auth:** Required (any role)  
**Path parameter:** `assessment_id` — UUID  
**Query parameter:** `format` — `json` (default) \| `html` \| `pdf`

#### Response

**302 Found** — Redirects to a pre-signed S3 URL for the requested report format.

The pre-signed URL expires after **24 hours**. To get a fresh URL, call this endpoint again — it always generates a new pre-signed URL pointing to the same stored report.

#### Error Responses

| HTTP Status | Error Code | When |
|---|---|---|
| 400 | `invalid_format` | `format` parameter is not one of `json`, `html`, `pdf` |
| 404 | `assessment_not_found` | No assessment with this ID |
| 404 | `report_not_ready` | Assessment exists but is not yet complete |
| 403 | `insufficient_permissions` | Assessment belongs to a different API key |

---

### 7.4 GET /api/v1/assess/{assessment_id}/audit

**Retrieve the full audit log for an assessment.**

**Auth:** Required — `reviewer` role only  
**Path parameter:** `assessment_id` — UUID

#### Response

**200 OK** — Returns `AuditLogResponse`.

```json
{
  "assessment_id": "a3f7c2d1-9b4e-4f2a-bc31-7d8e9f1a2b3c",
  "total_events": 22,
  "events": [
    {
      "log_id": "001e2f3a-4b5c-6d7e-8f9a-0b1c2d3e4f5a",
      "event_type": "assessment_submitted",
      "event_timestamp": "2026-06-18T10:30:00Z",
      "component": "api",
      "event_detail": {
        "file_format": "csv",
        "file_size_bytes": 45231890,
        "file_sha256": "a3f7c2..."
      },
      "severity": "INFO"
    },
    {
      "log_id": "002e2f3a-4b5c-6d7e-8f9a-0b1c2d3e4f5a",
      "event_type": "profiling_complete",
      "event_timestamp": "2026-06-18T10:30:48Z",
      "component": "profiler",
      "event_detail": {
        "rows": 12450,
        "columns": 38,
        "pii_detected": false,
        "icd_codes_found": true,
        "overall_completeness_pct": 94.2
      },
      "severity": "INFO"
    }
  ]
}
```

#### Error Responses

| HTTP Status | Error Code | When |
|---|---|---|
| 403 | `insufficient_permissions` | Caller has `submitter` role |
| 404 | `assessment_not_found` | No assessment with this ID |

---

### 7.5 GET /api/v1/datasets/{dataset_id}/assessments

**List all assessments for a given AIKosh dataset ID.**

**Auth:** Required (any role)  
**Path parameter:** `dataset_id` — AIKosh dataset ID string (e.g. `"aikosh-hrd-00421"`)  
**Query parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `limit` | integer | 10 | Max records to return (1–50) |
| `offset` | integer | 0 | Records to skip |
| `status` | string | all | Filter by status: `queued` \| `processing` \| `complete` \| `failed` |

#### Response

**200 OK:**

```json
{
  "dataset_id": "aikosh-hrd-00421",
  "total": 3,
  "limit": 10,
  "offset": 0,
  "assessments": [
    {
      "assessment_id": "a3f7c2d1-9b4e-4f2a-bc31-7d8e9f1a2b3c",
      "status": "complete",
      "submitted_at": "2026-06-18T10:30:00Z",
      "completed_at": "2026-06-18T10:34:22Z",
      "cqi": 67.9,
      "cqi_band": "Silver",
      "prs": 22,
      "release_classification": "Controlled",
      "toolkit_version": "1.0.0"
    },
    {
      "assessment_id": "b4e8d3c2-0a5f-4g3b-cd42-8e9f0a1b2c3d",
      "status": "complete",
      "submitted_at": "2026-05-10T08:15:00Z",
      "completed_at": "2026-05-10T08:19:11Z",
      "cqi": 55.4,
      "cqi_band": "Silver",
      "prs": 22,
      "release_classification": "Controlled",
      "toolkit_version": "1.0.0"
    }
  ]
}
```

#### Error Responses

| HTTP Status | Error Code | When |
|---|---|---|
| 404 | `dataset_not_found` | No assessments exist for this dataset ID |
| 400 | `invalid_limit` | `limit` is outside 1–50 range |

---

### 7.6 GET /api/v1/health

**Service health check.**

**Auth:** Not required  
**Purpose:** Used by load balancer, Kubernetes liveness/readiness probes, and monitoring.

#### Response

**200 OK** when healthy or degraded. **503 Service Unavailable** when unhealthy.

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-06-18T10:00:00Z",
  "dependencies": {
    "postgres": "ok",
    "redis": "ok",
    "s3": "ok",
    "celery_workers": "ok"
  }
}
```

**Degraded example** (Redis slow but functional):
```json
{
  "status": "degraded",
  "version": "1.0.0",
  "timestamp": "2026-06-18T10:00:00Z",
  "dependencies": {
    "postgres": "ok",
    "redis": "ok",
    "s3": "ok",
    "celery_workers": "no_workers"
  }
}
```

**Status logic:**

| Condition | `status` |
|---|---|
| All dependencies `"ok"` | `"healthy"` |
| Any dependency `"error"` but service can partially respond | `"degraded"` |
| PostgreSQL `"error"` OR all Celery workers down | `"unhealthy"` (503) |

---

## 8. Webhook Contract (AIKosh Inbound)

When an assessment completes, the toolkit POSTs quality metadata to the AIKosh webhook URL. This section documents the payload AIKosh must be prepared to receive.

**Method:** POST  
**Content-Type:** `application/json`  
**Auth header sent by toolkit:**
```
Authorization: Bearer <AIKOSH_WEBHOOK_SECRET>
X-Toolkit-Version: 1.0.0
X-Assessment-ID: <assessment_id>
```

**Expected AIKosh response:** HTTP 200 or 201. Any 4xx or 5xx triggers retry.

**Retry schedule:** 3 retries at 30s, 120s, 480s (exponential backoff).

**Webhook payload:**

```json
{
  "assessment_id": "a3f7c2d1-9b4e-4f2a-bc31-7d8e9f1a2b3c",
  "dataset_id": "aikosh-hrd-00421",
  "assessed_at": "2026-06-18T10:34:22Z",
  "toolkit_version": "1.0.0",
  "cqi": 67.9,
  "cqi_band": "Silver",
  "prs": 22,
  "prs_band": "Moderate",
  "release_classification": "Controlled",
  "domain_11_applicable": false,
  "domain_scores": {
    "1_annotation_labelling_reliability":  { "score": 3, "confidence": "Medium" },
    "2_metadata_completeness":             { "score": 3, "confidence": "High"   },
    "3_documentation_user_guidance":       { "score": 2, "confidence": "High"   },
    "4_population_representativeness":     { "score": 3, "confidence": "Medium" },
    "5_data_structure_interoperability":   { "score": 3, "confidence": "High"   },
    "6_ai_analytics_readiness":            { "score": 2, "confidence": "High"   },
    "7_privacy_identifiability":           { "score": 4, "confidence": "High"   },
    "8_security_access_governance":        { "score": 3, "confidence": "Low"    },
    "9_provenance_workflow_transparency":  { "score": 2, "confidence": "Medium" },
    "10_ethical_social_accountability":    { "score": 3, "confidence": "Medium" },
    "11_synthetic_simulated_data":         { "score": null, "confidence": null  },
    "12_stewardship_governance":           { "score": 3, "confidence": "Low"    },
    "13_model_linkage_integrity":          { "score": 3, "confidence": "Low"    },
    "14_environmental_sustainability":     { "score": 1, "confidence": "Low"    },
    "15_continuous_curation_feedback":     { "score": 2, "confidence": "Medium" }
  },
  "report_url": "https://toolkit.aikosh.gov.in/api/v1/assess/a3f7c2d1.../report?format=pdf",
  "audit_log_id": "b7e2a1f3-4c9d-4e0b-8a2c-1d7f3e8b9c0a"
}
```

**Idempotency note:** If AIKosh receives the same `assessment_id` more than once (due to retries), it should update the existing record rather than create a duplicate. The payload is identical on retries.

---

## 9. Error Reference

Complete list of all machine-readable error codes.

| Error Code | HTTP Status | Description |
|---|---|---|
| `missing_auth_header` | 401 | `Authorization` header not present |
| `invalid_api_key` | 401 | API key not found or inactive |
| `insufficient_permissions` | 403 | API key role does not permit this operation |
| `missing_file` | 400 | No file uploaded in the request |
| `missing_metadata` | 400 | No metadata JSON in the request |
| `file_too_large` | 413 | File exceeds 5GB size limit |
| `unsupported_format` | 422 | File format not in accepted list |
| `encoding_error` | 422 | File encoding cannot be auto-detected |
| `validation_error` | 422 | Metadata form fails Pydantic schema validation |
| `invalid_format` | 400 | `format` query param not `json`/`html`/`pdf` |
| `invalid_limit` | 400 | `limit` outside 1–50 range |
| `assessment_not_found` | 404 | No assessment with this ID |
| `report_not_ready` | 404 | Assessment not yet complete, report unavailable |
| `dataset_not_found` | 404 | No assessments found for this dataset ID |
| `rate_limit_exceeded` | 429 | Over 100 requests/minute |
| `concurrent_limit_exceeded` | 429 | Over 10 concurrent active assessments |
| `internal_error` | 500 | Unexpected server error |
| `service_unavailable` | 503 | Service unhealthy (database or critical dependency down) |

---

## 10. Enum Reference

### Assessment Status
| Value | Meaning |
|---|---|
| `queued` | Job received, waiting for Celery worker |
| `processing` | Celery worker actively running assessment |
| `complete` | Assessment finished successfully |
| `failed` | Assessment failed; see `error_message` |

### CQI Band
| Value | CQI Range | Meaning |
|---|---|---|
| `Diamond` | ≥ 95 | Global exemplar |
| `Platinum` | 85–94 | Best-practice dataset |
| `Gold` | 70–84 | High-quality dataset |
| `Silver` | 50–69 | Permissible, needs improvement |
| `Bronze` | 25–49 | Embargoed for enhancement |
| `Remediation` | < 25 | Iterative QA required |

### PRS Band
| Value | PRS Range | Risk Level |
|---|---|---|
| `Low` | 0–15 | Minimal re-identification risk |
| `Moderate` | 16–40 | Some residual risk |
| `High` | 41–70 | Significant risk |
| `Very High` | 71–100 | Severe risk |

### Release Classification
| Value | Meaning |
|---|---|
| `Open` | Publicly accessible; minimal privacy risk |
| `Controlled` | Access via Data Use Agreement; moderate risk or quality |
| `Restricted` | Tightly controlled; high privacy risk or very low quality |

### Sensitivity Class
| Value | Examples | PRS Multiplier |
|---|---|---|
| `standard` | General epidemiological, demographic, non-stigma health data | 1.0× |
| `high_stigma` | TB, HIV, reproductive health, mental health, genomic, caste/tribe, violence | 1.5× |
| `critical` | Forensic, detainee, conflict-zone, tribal GPS, refugee, protest-related | 2.0× |

### Confidence Level (per domain score)
| Value | Meaning |
|---|---|
| `High` | Score primarily from direct data file analysis |
| `Medium` | Score from mix of data analysis and metadata form |
| `Low` | Score entirely from metadata form (cannot be verified from file) |

### Audit Event Types
| Event Type | Component |
|---|---|
| `assessment_submitted` | api |
| `file_stored_s3` | api |
| `profiling_started` | profiler |
| `profiling_complete` | profiler |
| `domain_scoring_started` | orchestrator |
| `domain_1_scored` through `domain_15_scored` | domain scorers |
| `cqi_computed` | cqi_engine |
| `prs_computed` | prs_engine |
| `release_classified` | release_engine |
| `report_generated` | report_generator |
| `dataset_file_deleted` | api |
| `assessment_complete` | worker |
| `aikosh_webhook_sent` | webhook |
| `aikosh_webhook_failed` | webhook |
| `assessment_failed` | worker |

---

## 11. YAML Specification

The following is the complete OpenAPI 3.1.0 YAML specification. This is the machine-readable form of everything defined above. Save as `openapi.yaml`.

```yaml
openapi: 3.1.0

info:
  title: AIKosh Dataset Quality Evaluation Toolkit API
  version: 1.0.0
  description: >
    Automated MIDAS-inspired quality assessment API for health research datasets
    on the AIKosh platform. Produces a Composite Quality Index (CQI),
    Privacy-Risk Score (PRS), and release classification for every submitted dataset.
  contact:
    name: AIKosh / IndiaAI Mission
    url: https://aikosh.indiaai.gov.in

servers:
  - url: https://toolkit.aikosh.gov.in
    description: Production
  - url: https://toolkit-staging.aikosh.gov.in
    description: Staging
  - url: http://localhost:8000
    description: Development

security:
  - BearerAuth: []
  - CookieAuth: []

components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: API Key
      description: "API key in format: tkt_live_{32chars}"
    CookieAuth:
      type: apiKey
      in: cookie
      name: session_token
      description: "JWT session token stored in HttpOnly cookie"

  schemas:

    # ── MetadataForm ───────────────────────────────────────────
    MetadataForm:
      type: object
      required:
        - dataset_name
        - dataset_type
        - study_type
        - target_population
        - geographic_coverage
        - sensitivity_class
      properties:
        dataset_name:
          type: string
          maxLength: 500
          example: "Multi-site TB Cohort Study India 2019-2023"
        dataset_version:
          type: string
          maxLength: 100
          example: "1.0.0"
        dataset_type:
          type: string
          enum: [tabular, imaging, text, multimodal]
        study_type:
          type: string
          enum: [RCT, cohort, cross_sectional, registry, observational, case_control, other]
        target_population:
          type: string
        geographic_coverage:
          type: string
          enum: [village, taluk, district, state, national, multi_country]
        age_range_min:
          type: integer
          minimum: 0
          maximum: 120
        age_range_max:
          type: integer
          minimum: 0
          maximum: 120
        sex_distribution:
          type: string
          enum: [male_only, female_only, both, not_specified]
        num_sites:
          type: integer
          minimum: 1
        collection_start_date:
          type: string
          format: date
        collection_end_date:
          type: string
          format: date
        annotation_methodology:
          type: string
        num_annotators:
          type: integer
          minimum: 1
        irr_method:
          type: string
          example: "Cohen's Kappa"
        irr_value:
          type: number
          minimum: 0
          maximum: 1
          example: 0.82
        standards_used:
          type: string
          example: "ICD-10"
        ethics_approval_ref:
          type: string
        consent_type:
          type: string
          enum: [individual, waiver, community, not_applicable]
        deidentification_method:
          type: string
        differential_privacy_applied:
          type: boolean
          default: false
        dp_epsilon:
          type: number
          minimum: 0
          exclusiveMinimum: true
          example: 0.5
        sensitivity_class:
          type: string
          enum: [standard, high_stigma, critical]
        persistent_identifier:
          type: string
          example: "10.5281/zenodo.9876543"
        license_type:
          type: string
          example: "CC BY 4.0"
        synthetic_data_pct:
          type: number
          minimum: 0
          maximum: 100
          default: 0
        access_control_method:
          type: string
        linked_model_ids:
          type: array
          items:
            type: string
        data_dictionary_uploaded:
          type: boolean
          default: false
        provenance_pipeline_available:
          type: boolean
          default: false
        github_repo_url:
          type: string
          format: uri
        changelog_provided:
          type: boolean
          default: false
        version_format:
          type: string
          enum: [semantic, arbitrary, none]
        sustainability_info_provided:
          type: boolean
          default: false
        feedback_mechanism_exists:
          type: boolean
          default: false
        aikosh_dataset_id:
          type: string
          example: "aikosh-hrd-00421"
        webhook_url:
          type: string
          format: uri

    # ── AssessmentSubmitResponse ───────────────────────────────
    AssessmentSubmitResponse:
      type: object
      properties:
        assessment_id:
          type: string
          format: uuid
        status:
          type: string
          enum: [queued]
        estimated_completion_seconds:
          type: integer
        poll_url:
          type: string
        submitted_at:
          type: string
          format: date-time

    # ── AssessmentStatusResponse ───────────────────────────────
    AssessmentStatusResponse:
      type: object
      properties:
        assessment_id:
          type: string
          format: uuid
        status:
          type: string
          enum: [queued, processing, complete, failed]
        dataset_id:
          type: string
          nullable: true
        submitted_at:
          type: string
          format: date-time
        started_at:
          type: string
          format: date-time
          nullable: true
        completed_at:
          type: string
          format: date-time
          nullable: true
        error_message:
          type: string
          nullable: true
        error_traceback:
          type: string
          nullable: true

    # ── DomainScoreObject ──────────────────────────────────────
    DomainScoreObject:
      type: object
      properties:
        domain_number:
          type: integer
          minimum: 1
          maximum: 15
        domain_name:
          type: string
        score:
          type: integer
          minimum: 0
          maximum: 4
          nullable: true
        max_score:
          type: integer
          enum: [4]
          nullable: true
        not_applicable:
          type: boolean
        confidence:
          type: string
          enum: [High, Medium, Low]
          nullable: true
        rationale:
          type: string
          nullable: true
        evidence_items:
          type: array
          items:
            type: string
        gaps:
          type: array
          items:
            type: string
        inferred:
          type: boolean

    # ── CQIResult ──────────────────────────────────────────────
    CQIResult:
      type: object
      properties:
        value:
          type: number
          minimum: 0
          maximum: 100
        band:
          type: string
          enum: [Diamond, Platinum, Gold, Silver, Bronze, Remediation]
        total_score:
          type: integer
        max_possible:
          type: integer
          enum: [56, 60]
        formula_trace:
          type: string

    # ── PRSResult ──────────────────────────────────────────────
    PRSResult:
      type: object
      properties:
        value:
          type: integer
          minimum: 0
          maximum: 100
        band:
          type: string
          enum: [Low, Moderate, High, Very High]
        baseline_risk:
          type: number
        sensitivity_class:
          type: string
          enum: [standard, high_stigma, critical]
        sensitivity_multiplier:
          type: number
          enum: [1.0, 1.5, 2.0]
        adjusted_risk:
          type: number
        computation_trace:
          type: string
        differential_privacy_applied:
          type: boolean
        epsilon:
          type: number
          nullable: true

    # ── ReleaseClassification ──────────────────────────────────
    ReleaseClassification:
      type: object
      properties:
        classification:
          type: string
          enum: [Open, Controlled, Restricted]
        justification:
          type: string
        policy_override_applied:
          type: boolean

    # ── ReportURLs ─────────────────────────────────────────────
    ReportURLs:
      type: object
      properties:
        json:
          type: string
          format: uri
        html:
          type: string
          format: uri
        pdf:
          type: string
          format: uri

    # ── ProfileSummary ─────────────────────────────────────────
    ProfileSummary:
      type: object
      properties:
        rows:
          type: integer
        columns:
          type: integer
        file_format:
          type: string
        file_size_bytes:
          type: integer
        overall_completeness_pct:
          type: number
        direct_identifiers_detected:
          type: boolean
        icd_codes_detected:
          type: boolean
        sampled:
          type: boolean
        sample_rows:
          type: integer
          nullable: true

    # ── AssessmentResultResponse ───────────────────────────────
    AssessmentResultResponse:
      type: object
      properties:
        assessment_id:
          type: string
          format: uuid
        status:
          type: string
          enum: [complete]
        dataset_id:
          type: string
          nullable: true
        dataset_name:
          type: string
        toolkit_version:
          type: string
        assessed_at:
          type: string
          format: date-time
        domain_11_applicable:
          type: boolean
        cqi:
          $ref: '#/components/schemas/CQIResult'
        prs:
          $ref: '#/components/schemas/PRSResult'
        release:
          $ref: '#/components/schemas/ReleaseClassification'
        domain_scores:
          type: array
          items:
            $ref: '#/components/schemas/DomainScoreObject'
          minItems: 15
          maxItems: 15
        profile_summary:
          $ref: '#/components/schemas/ProfileSummary'
        report_urls:
          $ref: '#/components/schemas/ReportURLs'
        audit_log_id:
          type: string
          format: uuid

    # ── AuditEvent ─────────────────────────────────────────────
    AuditEvent:
      type: object
      properties:
        log_id:
          type: string
          format: uuid
        event_type:
          type: string
        event_timestamp:
          type: string
          format: date-time
        component:
          type: string
          nullable: true
        event_detail:
          type: object
          additionalProperties: true
        severity:
          type: string
          enum: [INFO, WARNING, ERROR]

    # ── AuditLogResponse ───────────────────────────────────────
    AuditLogResponse:
      type: object
      properties:
        assessment_id:
          type: string
          format: uuid
        total_events:
          type: integer
        events:
          type: array
          items:
            $ref: '#/components/schemas/AuditEvent'

    # ── AssessmentListItem ─────────────────────────────────────
    AssessmentListItem:
      type: object
      properties:
        assessment_id:
          type: string
          format: uuid
        status:
          type: string
          enum: [queued, processing, complete, failed]
        submitted_at:
          type: string
          format: date-time
        completed_at:
          type: string
          format: date-time
          nullable: true
        cqi:
          type: number
          nullable: true
        cqi_band:
          type: string
          nullable: true
        prs:
          type: integer
          nullable: true
        release_classification:
          type: string
          nullable: true
        toolkit_version:
          type: string

    # ── HealthResponse ─────────────────────────────────────────
    HealthResponse:
      type: object
      properties:
        status:
          type: string
          enum: [healthy, degraded, unhealthy]
        version:
          type: string
        timestamp:
          type: string
          format: date-time
        dependencies:
          type: object
          properties:
            postgres:
              type: string
              enum: [ok, error]
            redis:
              type: string
              enum: [ok, error]
            s3:
              type: string
              enum: [ok, error]
            celery_workers:
              type: string
              enum: [ok, no_workers, error]

    # ── ErrorResponse ──────────────────────────────────────────
    ErrorResponse:
      type: object
      properties:
        error:
          type: string
        message:
          type: string
        detail:
          type: object
          nullable: true
          additionalProperties: true
        request_id:
          type: string
          format: uuid

# ── Paths ──────────────────────────────────────────────────────
paths:

  /api/v1/assess/upload-url:
    post:
      summary: Request pre-signed upload URL
      operationId: getUploadUrl
      tags: [Assessment]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [filename, file_format]
              properties:
                filename:
                  type: string
                file_format:
                  type: string
      responses:
        '200':
          description: Upload URL generated successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  upload_url:
                    type: string
                  file_key:
                    type: string
                  assessment_id:
                    type: string
                    format: uuid

  /api/v1/assess:
    post:
      summary: Submit assessment details
      operationId: submitAssessment
      tags: [Assessment]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [file_key, metadata]
              properties:
                file_key:
                  type: string
                metadata:
                  $ref: '#/components/schemas/MetadataForm'
                data_dictionary_key:
                  type: string
                  nullable: true
                sop_key:
                  type: string
                  nullable: true
                consent_doc_key:
                  type: string
                  nullable: true
                pipeline_script_key:
                  type: string
                  nullable: true
      responses:
        '202':
          description: Assessment queued
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AssessmentSubmitResponse'
        '400':
          description: Missing parameters or key not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '429':
          description: Rate limit exceeded
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /api/v1/assess/{assessment_id}:
    get:
      summary: Get assessment status or full results
      operationId: getAssessment
      tags: [Assessment]
      parameters:
        - name: assessment_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Assessment status or complete result
          content:
            application/json:
              schema:
                oneOf:
                  - $ref: '#/components/schemas/AssessmentStatusResponse'
                  - $ref: '#/components/schemas/AssessmentResultResponse'
        '403':
          description: Assessment belongs to different API key
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '404':
          description: Assessment not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /api/v1/assess/{assessment_id}/report:
    get:
      summary: Download the quality assessment report
      operationId: getReport
      tags: [Reports]
      parameters:
        - name: assessment_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
        - name: format
          in: query
          required: false
          schema:
            type: string
            enum: [json, html, pdf]
            default: json
      responses:
        '302':
          description: Redirect to pre-signed S3 URL (24-hour expiry)
          headers:
            Location:
              schema:
                type: string
                format: uri
        '400':
          description: Invalid format parameter
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '404':
          description: Assessment not found or report not ready
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /api/v1/assess/{assessment_id}/audit:
    get:
      summary: Retrieve the full audit log for an assessment
      operationId: getAuditLog
      tags: [Audit]
      security:
        - BearerAuth: []
        - CookieAuth: []
      parameters:
        - name: assessment_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Audit log
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AuditLogResponse'
        '403':
          description: Insufficient permissions (submitter role)
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '404':
          description: Assessment not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /api/v1/datasets/{dataset_id}/assessments:
    get:
      summary: List all assessments for a dataset
      operationId: listDatasetAssessments
      tags: [Assessment]
      parameters:
        - name: dataset_id
          in: path
          required: true
          schema:
            type: string
        - name: limit
          in: query
          required: false
          schema:
            type: integer
            minimum: 1
            maximum: 50
            default: 10
        - name: offset
          in: query
          required: false
          schema:
            type: integer
            minimum: 0
            default: 0
        - name: status
          in: query
          required: false
          schema:
            type: string
            enum: [queued, processing, complete, failed]
      responses:
        '200':
          description: List of assessments
          content:
            application/json:
              schema:
                type: object
                properties:
                  dataset_id:
                    type: string
                  total:
                    type: integer
                  limit:
                    type: integer
                  offset:
                    type: integer
                  assessments:
                    type: array
                    items:
                      $ref: '#/components/schemas/AssessmentListItem'
        '404':
          description: No assessments found for this dataset
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /api/v1/auth/register:
    post:
      summary: Register a new user account
      operationId: registerUser
      tags: [Authentication]
      security: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - email
                - password
              properties:
                email:
                  type: string
                  format: email
                  example: user@example.com
                password:
                  type: string
                  format: password
                  minLength: 8
                  pattern: "^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)(?=.*[@$!%*?&])[A-Za-z\\d@$!%*?&]{8,}$"
                  description: "Must contain at least 8 characters, one uppercase, one lowercase, one number, and one special character."
                  example: "SecureP@ss123"
      responses:
        '201':
          description: User registered successfully, session cookie set
          headers:
            Set-Cookie:
              schema:
                type: string
                example: session_token=...; HttpOnly; Secure; SameSite=Lax
          content:
            application/json:
              schema:
                type: object
                properties:
                  user_id:
                    type: string
                    format: uuid
                    example: a3f7c2d1-9b4e-4f2a-bc31-7d8e9f1a2b3c
                  email:
                    type: string
                    format: email
                    example: user@example.com
        '400':
          description: Invalid email or password, or user already exists
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /api/v1/auth/login:
    post:
      summary: Login and receive session token cookie
      operationId: loginUser
      tags: [Authentication]
      security: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - email
                - password
              properties:
                email:
                  type: string
                  format: email
                  example: user@example.com
                password:
                  type: string
                  format: password
                  minLength: 8
                  pattern: "^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)(?=.*[@$!%*?&])[A-Za-z\\d@$!%*?&]{8,}$"
                  description: "Must contain at least 8 characters, one uppercase, one lowercase, one number, and one special character."
                  example: "SecureP@ss123"
      responses:
        '200':
          description: Login successful, session cookie set
          headers:
            Set-Cookie:
              schema:
                type: string
                example: session_token=...; HttpOnly; Secure; SameSite=Lax
          content:
            application/json:
              schema:
                type: object
                properties:
                  message:
                    type: string
                    example: Login successful
        '401':
          description: Invalid credentials
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /api/v1/auth/logout:
    post:
      summary: Log out and clear session cookie
      operationId: logoutUser
      tags: [Authentication]
      security:
        - CookieAuth: []
      responses:
        '200':
          description: Logged out successfully, session cookie cleared
          headers:
            Set-Cookie:
              schema:
                type: string
                example: session_token=; Max-Age=0; HttpOnly; Secure; SameSite=Lax
          content:
            application/json:
              schema:
                type: object
                properties:
                  message:
                    type: string
                    example: Logged out successfully
        '401':
          description: Not authenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /api/v1/auth/keys:
    get:
      summary: List all active developer API keys for the current user
      operationId: listApiKeys
      tags: [Authentication]
      security:
        - CookieAuth: []
      responses:
        '200':
          description: List of active API keys retrieved successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  keys:
                    type: array
                    items:
                      type: object
                      properties:
                        key_id:
                          type: string
                          format: uuid
                          example: b4e8c9d1-0f3a-4e2b-9c31-8d9e0f1a2b3c
                        key_prefix:
                          type: string
                          example: tkt_live_ab12
                        created_at:
                          type: string
                          format: date-time
                          example: 2026-06-18T10:30:00Z
                        last_used_at:
                          type: string
                          format: date-time
                          nullable: true
                          example: 2026-06-18T11:45:00Z
                        expires_at:
                          type: string
                          format: date-time
                          nullable: true
        '401':
          description: Not authenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

    post:
      summary: Generate a new database-backed developer API key
      operationId: createApiKey
      tags: [Authentication]
      security:
        - CookieAuth: []
      responses:
        '201':
          description: Developer API key generated successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  key_id:
                    type: string
                    format: uuid
                    example: b4e8c9d1-0f3a-4e2b-9c31-8d9e0f1a2b3c
                  key_prefix:
                    type: string
                    example: tkt_live_ab12
                  raw_key:
                    type: string
                    example: tkt_live_ab12cd34ef56gh78ij90kl12mn34op56
                  created_at:
                    type: string
                    format: date-time
                    example: 2026-06-18T10:30:00Z
                  expires_at:
                    type: string
                    format: date-time
                    nullable: true
        '401':
          description: Not authenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /api/v1/auth/keys/{key_id}:
    delete:
      summary: Revoke / delete a developer API key
      operationId: revokeApiKey
      tags: [Authentication]
      security:
        - CookieAuth: []
      parameters:
        - name: key_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: API key revoked successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  message:
                    type: string
                    example: API key revoked successfully
        '401':
          description: Not authenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '404':
          description: API key not found or belongs to another user
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /api/v1/admin/users:
    get:
      summary: List all registered users (Admin only)
      operationId: listUsers
      tags: [Admin]
      security:
        - CookieAuth: []
      responses:
        '200':
          description: List of registered users retrieved successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  users:
                    type: array
                    items:
                      type: object
                      properties:
                        user_id:
                          type: string
                          format: uuid
                          example: a3f7c2d1-9b4e-4f2a-bc31-7d8e9f1a2b3c
                        email:
                          type: string
                          format: email
                          example: user@example.com
                        role:
                          type: string
                          example: user
                        is_active:
                          type: boolean
                          example: true
                        created_at:
                          type: string
                          format: date-time
                          example: 2026-06-18T10:30:00Z
        '401':
          description: Not authenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '403':
          description: Insufficient permissions (Admin only)
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /api/v1/admin/users/{user_id}/toggle-active:
    post:
      summary: Suspend or reactivate user account (Admin only)
      operationId: toggleUserActive
      tags: [Admin]
      security:
        - CookieAuth: []
      parameters:
        - name: user_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: User state toggled successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  user_id:
                    type: string
                    format: uuid
                    example: a3f7c2d1-9b4e-4f2a-bc31-7d8e9f1a2b3c
                  is_active:
                    type: boolean
                    example: false
        '401':
          description: Not authenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '403':
          description: Insufficient permissions (Admin only)
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '404':
          description: User not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /api/v1/health:
    get:
      summary: Service health check
      operationId: getHealth
      tags: [System]
      security: []
      responses:
        '200':
          description: Service is healthy or degraded
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HealthResponse'
        '503':
          description: Service is unhealthy
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HealthResponse'
```

---

*End of Document*

---

**Document History**

| Version | Date | Author | Notes |
|---|---|---|---|
| 1.0 | June 18, 2026 | — | Initial OpenAPI specification based on PRD v1.0 and TDD v1.0 |
| 1.1 | June 24, 2026 | — | Realigned to full-stack app. Updated §1 (API Overview: added web UI users as primary consumer), flagged implementation mismatch in §7.2 (target: pre-signed URL + file_key; current: multipart/form-data — migration required). Updated references to PRD v1.1 and TDD v1.1. |
