# 5-Layer Systematic Bug Audit Report — AIKosh Dataset Quality Toolkit

**Audit Date:** 28 Jun 2026
**Auditor:** Antigravity (Claude Opus 4.6)
**Scope:** Full-stack static code audit — 15 domain scorers, 3 scoring engines, profiler, 7 API routes, 4 frontend files, 8 DB models, 3 reference docs
**Method:** Detection-only. Every bug is falsifiable: `File X at line Y produces behavior Z that violates requirement R.`

---

## Executive Summary

| Severity | Count |
|----------|-------|
| **CRITICAL (breaks scores)** | 8 |
| **HIGH (contract violation)** | 12 |
| **MEDIUM (logic gap)** | 15 |
| **LOW (drift/cosmetic)** | 10 |
| **TOTAL** | **45** |

---

## Remediation Strategy & Strict Test Integrity Rules

### Strict Rule for Test Modifications
To guarantee tests are never loosened to hide codebase bugs, every test assertion change will be explicitly proved against [OpenAPI.md](docs/OpenAPI.md), [Questionnaire.md](docs/Questionnaire.md), [TDD.md](docs/TDD_AIKosh_Dataset_Quality_Toolkit.md), or [PRD.md](docs/PRD_AIKosh_Dataset_Quality_Toolkit.md). If a test fails, I will check the doc authority hierarchy first; if the codebase violates the doc, I will fix the codebase. Test files will only be updated when the test itself contained an illegal assertion (such as expecting `score == 0` when MIDAS docs enforce `1–4`), and I will show you the exact line in the docs before touching any test.

### Remediation Batch Grouping Strategy
Bugs are executed in 5 sequential, layer-based batches following data dependency order:
1. **Batch 1 (Score Range & Scaling Integrity — COMPLETED):** Resolved 8 bugs eliminating `score=0` across D01, D03, D05, D07, D10, worker fallback, DB check constraints, and dynamic CQI max calculation.
2. **Batch 2 (Core Scorer & YAML Wiring):** Fix D06 phantom profiler key and bind PRS, CQI, and Release Classifier directly to `domain_criteria.yaml` so scoring logic is fully dynamic.
3. **Batch 3 (Input Hygiene & Sanitation):** Add `.strip()` checks across all 8 string-parsing scorers and fix profiler edge cases (empty dataframes, single-row `NaN` standard deviations).
4. **Batch 4 (DB Models & Schema Alignment):** Add missing database columns (`sustainability_info_provided`, `feedback_mechanism_exists`), align ORM nullability with Pydantic, and replace hardcoded workspace paths.
5. **Batch 5 (Frontend Types & Client Alignment):** Align TypeScript interfaces in `index.ts` with backend Pydantic models and add missing HTTP methods (`PUT`) and error handlers in `client.ts`.

### Required Output Format per Bug Fix
Every fixed bug in each batch must be reported using this strict format:
```
Bug X <filename>:<line>
  Diff: -old_code +new_code
  Proof: grep returned no matches
  Why: reason for fix aligned with docs
```

---

## Layer 1: Invariant Checks

---

### I1: Score Range Invariant — FAIL

> **Rule:** Every `score` value must be in {1, 2, 3, 4} or `not_applicable=True`.

| # | File | Line | Score Value | Verdict |
|---|------|------|-------------|---------|
| 1 | [domain_01_annotation.py](backend/app/engine/domains/domain_01_annotation.py#L24) | 24 | `score=0` | Returns 0 when annotation_methodology missing |
| 2 | [domain_03_documentation.py](backend/app/engine/domains/domain_03_documentation.py#L41) | 41 | `score = items` where items starts at 0 | Returns 0 when all 4 docs missing |
| 3 | [domain_05_interoperability.py](backend/app/engine/domains/domain_05_interoperability.py#L28) | 28 | `score = 0` | Returns 0 when completeness < 50% |
| 4 | [domain_07_privacy.py](backend/app/engine/domains/domain_07_privacy.py#L21) | 21 | `score=0` | Returns 0 when direct PII detected |
| 5 | [domain_10_ethics.py](backend/app/engine/domains/domain_10_ethics.py#L19) | 19 | `score = 0` | Returns 0 when both ethics + consent missing |
| 6 | [tasks.py](backend/app/worker/tasks.py#L211) | 211 | `score_val = 0` | Error fallback defaults to score=0 |

**Additional finding — DB CHECK constraint allows it:**
[domain_score.py](backend/app/models/domain_score.py#L13) line 13: `CheckConstraint('score >= 0 AND score <= 4')` allows `score=0` at the DB level. Should be `score >= 1 AND score <= 4` with NULL permitted for N/A.

**I1 Result: FAIL — 6 violations (5 scorers + 1 worker fallback) + 1 DB constraint bug**

---

### I2: YAML Threshold Invariant — FAIL

> **Rule:** Every numerical threshold in a scorer must come from `self.criteria`, not hardcoded.

| # | File | Line | Hardcoded Value | YAML Key (should use) |
|---|------|------|-----------------|----------------------|
| 1 | [domain_02_metadata.py](backend/app/engine/domains/domain_02_metadata.py#L27) | 27-33 | `30`, `60`, `85` | No YAML thresholds for D2 |
| 2 | [domain_05_interoperability.py](backend/app/engine/domains/domain_05_interoperability.py#L26) | 26 | `50.0` | Not in YAML |
| 3 | [domain_14_sustainability.py](backend/app/engine/domains/domain_14_sustainability.py#L21) | 21 | `10000000` (10MB) | No YAML thresholds for D14 |
| 4 | [prs.py](backend/app/engine/scoring/prs.py#L4) | 4-14 | `SENSITIVITY_MULTIPLIERS`, `PRS_BANDS` | YAML has values but Python hardcodes |
| 5 | [prs.py](backend/app/engine/scoring/prs.py#L42) | 42 | `50.0` (direct identifiers baseline) | Not in YAML |
| 6 | [prs.py](backend/app/engine/scoring/prs.py#L47) | 47 | `20.0` (DP epsilon multiplier) | Not in YAML |
| 7 | [prs.py](backend/app/engine/scoring/prs.py#L53) | 53-62 | `30.0`, `15.0`, `5.0` (location risks) | Hardcoded |
| 8 | [cqi.py](backend/app/engine/scoring/cqi.py#L4) | 4-11 | CQI_BANDS `95, 85, 70, 50, 25` | YAML has cqi_bands but Python hardcodes |
| 9 | [cqi.py](backend/app/engine/scoring/cqi.py#L25) | 25 | `60` / `56` | Should be `4 * len(active_domains)` |
| 10 | [release_classifier.py](backend/app/engine/scoring/release_classifier.py#L35) | 35 | `70.0` (open CQI min) | YAML has `release.open_cqi_min: 70` but code hardcodes |
| 11 | [domain_11_synthetic.py](backend/app/engine/domains/domain_11_synthetic.py#L39) | 39 | `50.0` (majority synthetic %) | No YAML threshold |

**I2 Result: FAIL — 11 violations. PRS, CQI, and release classifier all ignore their YAML config sections entirely.**

---

### I3: Metadata Key Existence Invariant — PASS

> **Rule:** Every `self.metadata.get("key")` in any scorer must match a MetadataForm field.

All metadata keys consumed by scorers cross-reference correctly to MetadataForm fields.

**I3 Result: PASS**

---

### I4: Whitespace/Empty-String False Positive Invariant — FAIL

> **Rule:** Whitespace-only strings (`"   "`) must not be treated as valid values.

| # | File | Line | Pattern | Impact |
|---|------|------|---------|--------|
| 1 | [domain_02_metadata.py](backend/app/engine/domains/domain_02_metadata.py#L20) | 20 | `if self.metadata.get(f):` for 10 key fields | Whitespace counts as filled |
| 2 | [domain_03_documentation.py](backend/app/engine/domains/domain_03_documentation.py#L12) | 12-14 | `bool(self.metadata.get(...))` | Whitespace is truthy |
| 3 | [domain_04_representativeness.py](backend/app/engine/domains/domain_04_representativeness.py#L15) | 15 | `if not geo:` | Whitespace passes check |
| 4 | [domain_05_interoperability.py](backend/app/engine/domains/domain_05_interoperability.py#L38) | 38 | `bool(declared_standards)` | Whitespace passes |
| 5 | [domain_08_security.py](backend/app/engine/domains/domain_08_security.py#L19) | 19 | `if not control:` | Whitespace enters keyword matching |
| 6 | [domain_09_provenance.py](backend/app/engine/domains/domain_09_provenance.py#L13) | 13 | truthiness check on version_format | Whitespace passes |
| 7 | [domain_10_ethics.py](backend/app/engine/domains/domain_10_ethics.py#L11) | 11 | `if not ethics:` | Whitespace passes |
| 8 | [domain_15_curation.py](backend/app/engine/domains/domain_15_curation.py#L11) | 11 | `if not repo:` | Whitespace passes |

**I4 Result: FAIL — 8 scorers lack `.strip()` protection. No scorer calls `.strip()` on any metadata string.**

---

### I5: Orphaned Schema Field Invariant — FAIL

> **Rule:** Every MetadataForm field must be consumed by at least 1 scorer.

| # | Orphaned Field | Line | Type |
|---|----------------|------|------|
| 1 | `age_range_min` | 16 | Optional[int] |
| 2 | `age_range_max` | 17 | Optional[int] |
| 3 | `collection_start_date` | 21 | Optional[date] |
| 4 | `collection_end_date` | 22 | Optional[date] |
| 5 | `direct_identifiers_present` | 37 | Optional[List[str]] |
| 6 | `temporal_granularity` | 40 | Optional[Literal] |
| 7 | `rare_condition_flag` | 41 | bool |
| 8 | `dp_epsilon` | 44 | Optional[float] |
| 9 | `dq_checks_applied` | 30 | Optional[List[str]] |
| 10 | `feedback_mechanism_exists` | 68 | bool |

**I5 Result: FAIL — 10 orphaned fields collected from users but never influence any domain score.**

---

### I6: Orphaned YAML Threshold Invariant — FAIL

> **Rule:** Every YAML threshold must be read by a scorer. Every scorer `.criteria.get()` must match a YAML key.

**Orphaned YAML keys (defined but never read):**

| # | YAML Path | Value | Expected Reader |
|---|-----------|-------|-----------------|
| 1 | domains.1.thresholds.min_annotators | 2 | [domain_01_annotation.py](backend/app/engine/domains/domain_01_annotation.py#L55) hardcodes `>= 2` |
| 2 | prs.sensitivity_multipliers | 1.0/1.5/2.0 | [prs.py](backend/app/engine/scoring/prs.py#L4) hardcodes dict |
| 3 | prs.bands | 15/40/70 | [prs.py](backend/app/engine/scoring/prs.py#L10) hardcodes list |
| 4 | cqi_bands | 95/85/70/50/25 | [cqi.py](backend/app/engine/scoring/cqi.py#L4) hardcodes list |
| 5 | release.open_cqi_min | 70 | [release_classifier.py](backend/app/engine/scoring/release_classifier.py#L35) hardcodes 70.0 |
| 6 | release.open_prs_band | "Low" | [release_classifier.py](backend/app/engine/scoring/release_classifier.py#L35) hardcodes "Low" |

**I6 Result: FAIL — 6 orphaned YAML keys configured but completely ignored.**

---

### I7: Profiler Contract Invariant — FAIL

> **Rule:** Every profiler output key must be consumed. Every scorer profile read must exist in profiler output.

**Orphaned profiler keys (produced but no scorer reads):**

| # | Profiler Key | Produced at Line |
|---|-------------|-----------------|
| 1 | `shape` | 89 |
| 2 | `columns` | 90 |
| 3 | `duplicates` | 93 |
| 4 | `split_columns` | 95 |
| 5 | `label_columns` | 96 |
| 6 | `age_distribution` | 97 |
| 7 | `schema_consistency` | 98 |

**Phantom scorer reads (scorer reads key profiler does not produce):**

| # | File | Line | Key Read |
|---|------|------|----------|
| 1 | [domain_06_ai_readiness.py](backend/app/engine/domains/domain_06_ai_readiness.py#L19) | 19 | `self.profile.get("statistical_summary", {}).get("max_class_imbalance_ratio")` — profiler produces `label_columns.imbalance_ratio` NOT `statistical_summary.max_class_imbalance_ratio` |

**I7 Result: FAIL — 7 orphaned profiler keys + 1 phantom read (D6 class imbalance NEVER evaluates)**

---

## Layer 2: Traceability Matrix

### Q5: Schema/Model Alignment — FAIL

| # | Pydantic Field | Pydantic Type | DB Column | DB Nullable | Issue |
|---|----------------|---------------|-----------|-------------|-------|
| 1 | standards_used | str (required) | standards_used | nullable=True | Pydantic requires but DB allows NULL |
| 2 | deidentification_method | str (required) | deidentification_method | nullable=True | Same issue |
| 3 | access_control_method | str (required) | access_control_method | nullable=True | Same issue |
| 4 | license_type | str (required) | license_type | nullable=True | Same issue |
| 5 | sustainability_info_provided | bool | — | — | NO DB column exists |
| 6 | feedback_mechanism_exists | bool | — | — | NO DB column exists |

> Bugs 5-6 mean these fields are stored ONLY in `raw_form_json` (if that merge works), not in dedicated columns.
> The `metadata_dict` construction in [tasks.py](backend/app/worker/tasks.py#L102) line 102 does `metadata_rec.__dict__` which reads ORM columns.
> These fields would be missing unless the raw_form_json merge at tasks.py:103-104 covers them.

---

## Layer 3: Cross-Doc Contract Verification

### 3A: Backend Issues

| # | Severity | File | Line | Issue |
|---|----------|------|------|-------|
| 1 | HIGH | [tasks.py](backend/app/worker/tasks.py#L69) | 69 | Hardcoded dev machine path `C:\Users\medha\OneDrive\Desktop\AI-KOSH-TOOLKIT` |
| 2 | MEDIUM | [tasks.py](backend/app/worker/tasks.py#L407) | 407 | Hardcoded `localhost:8000` in webhook report_url |

### 3C: Frontend Contract Issues

| # | Severity | File | Line | Issue |
|---|----------|------|------|-------|
| 1 | MEDIUM | [index.ts](frontend/lib/types/index.ts#L39) | 39 | `standards_used?: string` optional in TS but required in Pydantic |
| 2 | MEDIUM | [index.ts](frontend/lib/types/index.ts#L42) | 42 | `deidentification_method?: string` optional in TS but required in Pydantic |
| 3 | MEDIUM | [index.ts](frontend/lib/types/index.ts#L62) | 62 | `access_control_method?: string` optional in TS but required in Pydantic |
| 4 | MEDIUM | [index.ts](frontend/lib/types/index.ts#L26) | 26 | `geographic_coverage?: string` optional in TS but required Literal in Pydantic |
| 5 | MEDIUM | [index.ts](frontend/lib/types/index.ts#L69) | 69 | Missing `sustainability_info_provided` and `feedback_mechanism_exists` from TS MetadataForm |
| 6 | LOW | [index.ts](frontend/lib/types/index.ts#L71) | 71-81 | Missing `inferred` field in TS DomainScore interface |
| 7 | LOW | [client.ts](frontend/lib/api/client.ts#L35) | 35-50 | No `put` method — admin toggle-active uses PUT |
| 8 | LOW | [client.ts](frontend/lib/api/client.ts#L17) | 17-26 | No 401/429 specific error handling |

---

## Layer 4: Boundary and Edge Case Analysis

### CQI Math Bug

[cqi.py](backend/app/engine/scoring/cqi.py#L25) line 25: `max_possible = 60 if domain_11_applicable else 56`

When a scorer crashes (returning score=0 via the worker fallback at [tasks.py](backend/app/worker/tasks.py#L211) line 211), the 0 is included in
`sum(scores.values())` but the denominator stays at 60. This doubly penalizes: total drops AND denominator
doesn't shrink.

### D06 Class Imbalance Never Triggers

[domain_06_ai_readiness.py](backend/app/engine/domains/domain_06_ai_readiness.py#L19) line 19 reads `self.profile.get("statistical_summary", {}).get("max_class_imbalance_ratio")`.
But profiler produces `label_columns.imbalance_ratio` at [profiler.py](backend/app/engine/profiler/profiler.py#L344) line 344, NOT `statistical_summary.max_class_imbalance_ratio`.
Class imbalance check NEVER fires. `class_imbalance_ratio` is always None.

### Profiler Edge Cases

- Empty DataFrame: Returns `overall_pct: 0.0` which triggers D05's score=0 path (I1 violation)
- Single-row CSV: `non_null.std()` returns NaN. Stored in profile JSON as non-finite float.

### PII False Positive

[profiler.py](backend/app/engine/profiler/profiler.py#L40) line 40-42: ID_PATTERNS regex `\b(id|uid|uuid|...)\b` matches any column named `id`. Surrogate
primary key columns (common in exported CSVs) will be flagged as PII. This doesn't trigger
`direct_identifiers_detected` (line 212 excludes `id_cols`) so it doesn't break D07 scoring, but it pollutes
the profile JSON with false PII flags.

---

## Full Bug Summary Table (Sorted by Severity)

| # | ID | Severity | Layer | File | Line | Description |
|---|-----|----------|-------|------|------|-------------|
| 1 | I1-01 | CRITICAL | L1 | [domain_01_annotation.py](backend/app/engine/domains/domain_01_annotation.py#L24) | 24 | Returns score=0 when annotation_methodology missing |
| 2 | I1-02 | CRITICAL | L1 | [domain_03_documentation.py](backend/app/engine/domains/domain_03_documentation.py#L41) | 41 | score = items can be 0 when all docs missing |
| 3 | I1-03 | CRITICAL | L1 | [domain_05_interoperability.py](backend/app/engine/domains/domain_05_interoperability.py#L28) | 28 | Returns score=0 when completeness < 50% |
| 4 | I1-04 | CRITICAL | L1 | [domain_07_privacy.py](backend/app/engine/domains/domain_07_privacy.py#L21) | 21 | Returns score=0 when direct PII detected |
| 5 | I1-05 | CRITICAL | L1 | [domain_10_ethics.py](backend/app/engine/domains/domain_10_ethics.py#L19) | 19 | Returns score=0 when ethics+consent missing |
| 6 | I1-06 | CRITICAL | L1 | [tasks.py](backend/app/worker/tasks.py#L211) | 211 | Worker error fallback assigns score_val = 0 |
| 7 | I1-08 | CRITICAL | L1 | [cqi.py](backend/app/engine/scoring/cqi.py#L25) | 25 | Hardcoded max_possible = 60/56 |
| 8 | I7-08 | CRITICAL | L1 | [domain_06_ai_readiness.py](backend/app/engine/domains/domain_06_ai_readiness.py#L19) | 19 | Reads phantom key statistical_summary.max_class_imbalance_ratio — class imbalance never evaluated |
| 9 | I1-07 | HIGH | L1 | [domain_score.py](backend/app/models/domain_score.py#L13) | 13 | DB CHECK allows score >= 0 instead of >= 1 |
| 10 | I2-01 | HIGH | L1 | [domain_02_metadata.py](backend/app/engine/domains/domain_02_metadata.py#L27) | 27-33 | Hardcoded 30/60/85 percentage tiers |
| 11 | I2-02 | HIGH | L1 | [domain_05_interoperability.py](backend/app/engine/domains/domain_05_interoperability.py#L26) | 26 | Hardcoded 50.0 floor |
| 12 | I2-03 | HIGH | L1 | [domain_14_sustainability.py](backend/app/engine/domains/domain_14_sustainability.py#L21) | 21 | Hardcoded 10000000 (10MB) |
| 13 | I2-04 | HIGH | L1 | [domain_11_synthetic.py](backend/app/engine/domains/domain_11_synthetic.py#L39) | 39 | Hardcoded 50.0 majority threshold |
| 14 | I2-05 | HIGH | L1 | [prs.py](backend/app/engine/scoring/prs.py#L4) | 4-62 | Entire PRS ignores YAML config |
| 15 | I2-06 | HIGH | L1 | [cqi.py](backend/app/engine/scoring/cqi.py#L4) | 4-11 | CQI bands ignore YAML config |
| 16 | I2-07 | HIGH | L1 | [release_classifier.py](backend/app/engine/scoring/release_classifier.py#L35) | 35 | Release thresholds ignore YAML |
| 17 | Q5-01 | HIGH | L2 | [metadata_form.py](backend/app/schemas/metadata_form.py#L67) / [dataset_metadata.py](backend/app/models/dataset_metadata.py#L67) | 67-68 | sustainability_info_provided and feedback_mechanism_exists have no DB columns |
| 18 | 3A-01 | HIGH | L3 | [tasks.py](backend/app/worker/tasks.py#L69) | 69 | Hardcoded dev machine path |
| 19 | Q5-02 | HIGH | L2 | [metadata_form.py](backend/app/schemas/metadata_form.py#L32) / [dataset_metadata.py](backend/app/models/dataset_metadata.py#L32) | 32-60 | 4 required Pydantic fields map to nullable DB columns |
| 20 | I2-08 | HIGH | L1 | [domain_01_annotation.py](backend/app/engine/domains/domain_01_annotation.py#L55) | 55 | Hardcodes >= 2 annotators instead of reading min_annotators from YAML |
| 21 | I4-01 | MEDIUM | L1 | (8 scorers) | Various | No .strip() on any metadata string check |
| 22 | I5-01 | MEDIUM | L1 | [metadata_form.py](backend/app/schemas/metadata_form.py#L16) | 16 | age_range_min never consumed by any scorer |
| 23 | I5-02 | MEDIUM | L1 | [metadata_form.py](backend/app/schemas/metadata_form.py#L17) | 17 | age_range_max never consumed by any scorer |
| 24 | I5-03 | MEDIUM | L1 | [metadata_form.py](backend/app/schemas/metadata_form.py#L21) | 21 | collection_start_date never consumed by any scorer |
| 25 | I5-04 | MEDIUM | L1 | [metadata_form.py](backend/app/schemas/metadata_form.py#L22) | 22 | collection_end_date never consumed by any scorer |
| 26 | I5-05 | MEDIUM | L1 | [metadata_form.py](backend/app/schemas/metadata_form.py#L37) | 37 | direct_identifiers_present never consumed (D7 uses profile) |
| 27 | I5-06 | MEDIUM | L1 | [metadata_form.py](backend/app/schemas/metadata_form.py#L40) | 40 | temporal_granularity never consumed by any scorer |
| 28 | I5-07 | MEDIUM | L1 | [metadata_form.py](backend/app/schemas/metadata_form.py#L30) | 30 | dq_checks_applied never consumed by any scorer |
| 29 | I5-08 | MEDIUM | L1 | [metadata_form.py](backend/app/schemas/metadata_form.py#L68) | 68 | feedback_mechanism_exists never consumed by any scorer |
| 30 | 3A-02 | MEDIUM | L3 | [tasks.py](backend/app/worker/tasks.py#L407) | 407 | Hardcoded localhost:8000 in webhook payload |
| 31 | 3C-01 | MEDIUM | L3 | [index.ts](frontend/lib/types/index.ts#L39) | 39 | standards_used optional in TS but required in backend |
| 32 | 3C-02 | MEDIUM | L3 | [index.ts](frontend/lib/types/index.ts#L42) | 42 | deidentification_method optional in TS but required in backend |
| 33 | 3C-03 | MEDIUM | L3 | [index.ts](frontend/lib/types/index.ts#L62) | 62 | access_control_method optional in TS but required in backend |
| 34 | 3C-04 | MEDIUM | L3 | [index.ts](frontend/lib/types/index.ts#L26) | 26 | geographic_coverage optional in TS but required in backend |
| 35 | L4-01 | MEDIUM | L4 | [profiler.py](backend/app/engine/profiler/profiler.py#L153) | 153 | Single-row CSV produces NaN std stored in profile JSON |
| 36 | I7-01 | LOW | L1 | [profiler.py](backend/app/engine/profiler/profiler.py#L89) | 89 | shape key produced but never consumed |
| 37 | I7-02 | LOW | L1 | [profiler.py](backend/app/engine/profiler/profiler.py#L90) | 90 | columns key produced but never consumed |
| 38 | I7-03 | LOW | L1 | [profiler.py](backend/app/engine/profiler/profiler.py#L93) | 93 | duplicates key produced but never consumed |
| 39 | I7-04 | LOW | L1 | [profiler.py](backend/app/engine/profiler/profiler.py#L95) | 95 | split_columns key produced but never consumed |
| 40 | I7-05 | LOW | L1 | [profiler.py](backend/app/engine/profiler/profiler.py#L96) | 96 | label_columns key produced but never consumed |
| 41 | I7-06 | LOW | L1 | [profiler.py](backend/app/engine/profiler/profiler.py#L97) | 97 | age_distribution key produced but never consumed |
| 42 | I7-07 | LOW | L1 | [profiler.py](backend/app/engine/profiler/profiler.py#L98) | 98 | schema_consistency key produced but never consumed |
| 43 | 3C-05 | LOW | L3 | [index.ts](frontend/lib/types/index.ts#L71) | 71-81 | Missing inferred field in TS DomainScore |
| 44 | 3C-06 | LOW | L3 | [client.ts](frontend/lib/api/client.ts#L35) | 35-50 | No put method in API client |
| 45 | 3C-07 | LOW | L3 | [client.ts](frontend/lib/api/client.ts#L17) | 17-26 | No 401/429 specific error handling |
