> **Product Goal:** A user-facing, browser-first web application for automated MIDAS-grade health dataset quality assessment — with a secure multi-tenant backend, async processing pipeline, and a REST API surface that external platforms (AIKosh) can integrate with programmatically.

# Product Requirements Document
# AIKosh Dataset Quality Evaluation Toolkit
### MIDAS-Inspired Automated Quality Assessment System for Health Research Datasets

---

**Document Version:** 1.1  
**Status:** Active  
**Last Updated:** June 24, 2026  
**Prepared For:** AIKosh / IndiaAI Mission  
**Classification:** Internal Working Document

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Background & Context](#2-background--context)
   - 2.1 What is AIKosh
   - 2.2 What is MIDAS 2.0
   - 2.3 The Integration Gap
   - 2.4 The IndiaAI–ICMR MoU Context
3. [MIDAS 2.0 Knowledge Extraction](#3-midas-20-knowledge-extraction)
   - 3.1 Framework Overview
   - 3.2 The Two-Stage Assessment Pathway
   - 3.3 The 15 Quality Domains (Complete)
   - 3.4 Scoring Methodology — Composite Quality Index (CQI)
   - 3.5 Scoring Methodology — Privacy-Risk Score (PRS)
   - 3.6 CQI × PRS Release Classification Matrix
   - 3.7 Expert Validation (Delphi) Process
   - 3.8 What Is Not Publicly Available
4. [AIKosh Platform Architecture Research](#4-aikosh-platform-architecture-research)
   - 4.1 Platform Overview
   - 4.2 Current Dataset Onboarding Workflow
   - 4.3 API & Integration Capabilities
   - 4.4 What AIKosh Currently Lacks
5. [Gap Analysis — MIDAS vs AIKosh](#5-gap-analysis--midas-vs-aikosh)
6. [Problem Statement](#6-problem-statement)
7. [Vision Statement](#7-vision-statement)
8. [Goals](#8-goals)
9. [Non-Goals](#9-non-goals)
10. [Success Metrics](#10-success-metrics)
11. [Stakeholders](#11-stakeholders)
12. [User Personas](#12-user-personas)
13. [User Stories](#13-user-stories)
14. [Proposed Solution Overview](#14-proposed-solution-overview)
15. [Functional Scope](#15-functional-scope)
16. [End-to-End User Journey](#16-end-to-end-user-journey)
17. [Module Specifications](#17-module-specifications)
    - 17.1 Dataset Upload & Ingestion Module
    - 17.2 Dataset Profiling Engine
    - 17.3 Quality Assessment Engine (15 Domains)
    - 17.4 CQI Calculation Engine
    - 17.5 PRS Calculation Engine
    - 17.6 Release Classification Engine
    - 17.7 Report Generation Module
    - 17.8 Dashboard & Visualisations
    - 17.9 AIKosh Integration Layer
18. [Quality Assessment Framework Specification](#18-quality-assessment-framework-specification)
    - 18.1 Domain-by-Domain Automated Metrics
    - 18.2 Scoring Ladder Per Domain
    - 18.3 CQI Formula & Performance Bands
    - 18.4 PRS Formula & Sensitivity Classification
    - 18.5 Release Matrix
    - 18.6 Assumptions & Inferences Made
19. [API Requirements](#19-api-requirements)
20. [System Architecture Overview](#20-system-architecture-overview)
21. [Data Flow](#21-data-flow)
22. [Database Design Overview](#22-database-design-overview)
23. [Supported Dataset Formats](#23-supported-dataset-formats)
24. [Non-Functional Requirements](#24-non-functional-requirements)
25. [Security & Privacy Requirements](#25-security--privacy-requirements)
26. [Testing Strategy](#26-testing-strategy)
27. [Acceptance Criteria](#27-acceptance-criteria)
28. [Risks & Limitations](#28-risks--limitations)
29. [Assumptions Log](#29-assumptions-log)
30. [Future Roadmap](#30-future-roadmap)
31. [Deliverables](#31-deliverables)
32. [Appendix A — MIDAS Domain Metric Catalog](#appendix-a--midas-domain-metric-catalog)
33. [Appendix B — Sample Quality Report Output](#appendix-b--sample-quality-report-output)
34. [Appendix C — PRS Calculation Worked Example](#appendix-c--prs-calculation-worked-example)
35. [Appendix D — Dataset Sources for Validation](#appendix-d--dataset-sources-for-validation)

---

## 1. Executive Summary

India's national AI ecosystem depends on high-quality, trustworthy health research datasets. The Indian Council of Medical Research (ICMR) has developed MIDAS 2.0 (Metric-based Integrity and Data Assessment System) — a rigorous, evidence-based framework for evaluating health research datasets across 15 quality domains, producing a Composite Quality Index (CQI) and a Privacy-Risk Score (PRS). However, MIDAS 2.0 is a manual, institution-facing process. It cannot be directly integrated into AIKosh — India's national AI dataset repository — in its current form.

This document defines the requirements for the **AIKosh Dataset Quality Evaluation Toolkit**: a **browser-first, full-stack web application** that operationalises the MIDAS 2.0 framework. Dataset custodians log in via the web UI, upload health research datasets, fill in a structured metadata form, and receive a comprehensive quality report across all 15 MIDAS domains — including a CQI, PRS, release classification, and downloadable audit report. AIKosh and other external platforms integrate programmatically via REST API, submitting datasets using API keys and receiving quality metadata via webhook on assessment completion.

The toolkit is not a replacement for ICMR's official MIDAS certification process. It is the **automated pre-assessment and continuous quality layer** that brings MIDAS-grade intelligence into the AIKosh dataset lifecycle.

---

## 2. Background & Context

### 2.1 What is AIKosh

AIKosh is the national AI dataset and model repository under India's IndiaAI Mission, housed at `aikosh.indiaai.gov.in`. It is one of seven strategic pillars of the IndiaAI Mission, approved by Cabinet in March 2024. As of early 2026, it hosts over 10,000 datasets across 20 sectors including health, agriculture, education, and governance.

AIKosh provides:
- A centralised, searchable repository of anonymised, India-relevant datasets
- API-based access for developers and researchers
- An AI Sandbox (integrated development environment) for model training and experimentation
- Standardised metadata submission and licensing management
- An open Expression of Interest (EOI) process for dataset contribution

All submissions to AIKosh are validated through both automated and manual backend processes prior to publication. Artefacts must be submitted with complete metadata, licensing information, and descriptive documentation.

### 2.2 What is MIDAS 2.0

MIDAS 2.0 (Metric-based Integrity and Data Assessment System) is a framework developed by ICMR to evaluate the quality, trustworthiness, and AI-readiness of **health research datasets** — data collected specifically for research purposes such as clinical trials, cohort studies, epidemiological surveys, biomedical registries, and observational studies. It is explicitly distinct from healthcare operational data (EHRs, hospital records, claims).

MIDAS 2.0 was developed as an upgrade over MIDAS 1.0, which was originally focused on medical imaging datasets. MIDAS 2.0 extends to multimodal biomedical and health data including tabular, text, voice, imaging, and EHR-linked datasets.

It evaluates datasets across **15 quality domains**, producing two output scores:
- **Composite Quality Index (CQI):** 0–100 scale, overall dataset quality
- **Privacy-Risk Score (PRS):** 0–100 scale, residual re-identification risk

Together, CQI and PRS determine a dataset's release classification: Open, Controlled, or Restricted.

### 2.3 The Integration Gap

MIDAS 2.0 is a **human-in-the-loop, institution-facing process** with two stages:

1. **Lite Version** — self-assessment completed by the dataset custodian (Independent Centre)
2. **Technical Version** — independent validation and final score computation by a Nodal Centre

This manual, two-party workflow cannot be directly plugged into AIKosh's automated dataset onboarding pipeline. There is:
- No public API for MIDAS assessment submission
- No programmatic scoring engine
- No GitHub repository or open-source implementation
- No machine-readable version of the framework

AIKosh currently performs generic metadata validation and manual compliance review, but has no mechanism to generate MIDAS-grade quality intelligence automatically.

### 2.4 The IndiaAI–ICMR MoU Context

In May 2026, IndiaAI and ICMR signed a Memorandum of Understanding establishing a structured collaboration. Under this MoU, ICMR committed to contributing anonymised, ethics-approved health research datasets, AI models, and toolkits developed under the MIDAS framework to AIKosh. This MoU explicitly acknowledges that MIDAS and AIKosh are complementary systems and that integration work is required to operationalise MIDAS assessments within AIKosh workflows.

The AIKosh Dataset Quality Evaluation Toolkit is the practical realisation of this integration commitment.

---

## 3. MIDAS 2.0 Knowledge Extraction

> This section documents everything publicly known about MIDAS 2.0, extracted from `midas.icmr.org.in`. It forms the factual foundation for all scoring logic in this toolkit.

### 3.1 Framework Overview

| Attribute | Value |
|---|---|
| Full Name | Metric-based Integrity and Data Assessment System 2.0 |
| Owner | Indian Council of Medical Research (ICMR) |
| Target Data | Health research datasets (not healthcare operational data) |
| Number of Domains | 15 |
| Scoring Outputs | CQI (0–100) + PRS (0–100) |
| Assessment Versions | Lite Version (self-assessment) + Technical Version (nodal validation) |
| Per-Domain Scale | 0–4 (0 = absent, 4 = exemplary) |
| Max Raw Score | 60 (15 domains × 4) |
| Performance Bands | 6 tiers (Remediation → Diamond) |
| Release Classes | Open / Controlled / Restricted |
| Public URL | https://midas.icmr.org.in |
| GitHub | None — no public codebase exists |

### 3.2 The Two-Stage Assessment Pathway

**Stage 1 — Lite Version (Self-Assessment by Independent Centre)**
- Dataset custodian performs structured self-assessment against 15 domains
- Uses simplified scoring options and ladders aligned to the Technical Version
- Custodian must retain all supporting evidence (SOPs, metadata, consent records, validation logs) for verification
- Produces a CQI-Lite and PRS-Lite (preliminary scores)
- Submitted to Nodal Centre for Stage 2

**Stage 2 — Technical Version (Validation by Nodal Centre)**
- Independent Nodal Centre verifies all Lite Version claims
- Requests clarifications or additional documentation where needed
- Applies detailed metrics, computation steps, and evidence-based validation
- Computes final CQI and PRS
- Recommends Open / Controlled / Restricted release classification
- Final report reviewed by Steering Committee before repository onboarding

### 3.3 The 15 Quality Domains (Complete)

All 15 domains are confirmed from the public Lite Version and Technical Version pages of midas.icmr.org.in. Each domain is scored 0–4 in both versions.

| # | Domain Name | Category | What It Measures |
|---|---|---|---|
| 1 | Annotation / Labelling Reliability | Data Quality | Quality and reliability of labels/annotations produced by experts or trained readers |
| 2 | Metadata Completeness | Data Quality | Rich, machine-actionable metadata with persistent identifiers to enable discovery and reuse |
| 3 | Documentation & User Guidance | Data Quality | Clarity and depth of human-readable documentation for context, methods, and reuse |
| 4 | Population Representativeness | Data Quality | How well the dataset reflects the intended population across sites, regions, age, sex, and other axes |
| 5 | Data Structure & Interoperability | Operational Readiness | Mapping to healthcare standards and automated data-quality checks: conformance, completeness, plausibility |
| 6 | AI / Analytics Readiness | Operational Readiness | Packaging for benchmarking and safeguards against data leakage and distribution shift |
| 7 | Privacy & Identifiability | Trust Safeguards | Risk that individuals can be re-identified or sensitive attributes can be inferred |
| 8 | Security & Access Governance | Trust Safeguards | Demonstrable operational security and auditability of access to data and systems |
| 9 | Provenance & Workflow Transparency | Trust Safeguards | End-to-end trace from raw data to release, with executable pipelines |
| 10 | Ethical & Social Accountability | Trust Safeguards | Processes for equity impact, stakeholder engagement, and redressal |
| 11 | Synthetic / Simulated Data *(if applicable)* | Trust Safeguards | Utility and privacy of synthetic data relative to real data |
| 12 | Stewardship & Governance | Trust Safeguards | Organisational readiness and compliance for responsible data stewardship |
| 13 | Model Linkage Integrity | Operational Readiness | Traceable and verifiable linkages between datasets and any released models |
| 14 | Environmental Sustainability | Operational Readiness | Measurement and management of energy and carbon footprints from storage and compute |
| 15 | Continuous Curation & Feedback | Operational Readiness | Release cadence, user feedback integration, and versioning discipline |

**Note on Domain 11:** Domain 11 (Synthetic / Simulated Data) is marked "if applicable." When a dataset contains no synthetic or simulated data, the CQI denominator is reduced to 56 (14 × 4) and the formula adjusted accordingly.

**Domain Groupings (from MIDAS 2.0 homepage):**
- **Data Quality (Domains 1–4):** Annotation fidelity, metadata, documentation, and completeness
- **Operational Readiness (Domains 5–6, 13–15):** Interoperability, AI-readiness, representativeness, sustainability
- **Trust Safeguards (Domains 7–12):** Governance, ethics, security, consent, and privacy risk

### 3.4 Scoring Methodology — Composite Quality Index (CQI)

**Per-Domain Scoring Ladder:**
Each domain is scored on a 0–4 ordinal ladder:
- **0** — Absent: No evidence of this quality dimension exists
- **1** — Minimal: Basic evidence exists but significantly incomplete
- **2** — Partial: Moderate implementation with notable gaps
- **3** — Adequate: Substantial compliance with minor gaps
- **4** — Exemplary: Fully implemented, well-evidenced, best-practice standard

Scoring rule: *"Use the highest level score where all statements are true. If any statement at that level is missing, step down one level."*

**CQI Formula (publicly available):**

```
CQI = (Sum of domain scores / 60) × 100
```

Where:
- Sum of domain scores = total points across all 15 domains (or 14 if Domain 11 is not applicable)
- Maximum possible = 60 (standard) or 56 (if Domain 11 is N/A)
- If Domain 11 is N/A: CQI = (Sum / 56) × 100

**CQI Performance Bands (6-Tier Grading):**

| Band | CQI Range | Interpretation |
|---|---|---|
| Diamond | ≥ 95 | Global exemplar |
| Platinum | 85–94 | Best-practice dataset |
| Gold | 70–84 | High-quality dataset |
| Silver | 50–69 | Permissible, needs improvement |
| Bronze | 25–49 | Embargoed for enhancement |
| Remediation | < 25 | Iterative QA required |

### 3.5 Scoring Methodology — Privacy-Risk Score (PRS)

The PRS estimates residual re-identification risk after privacy protections have been applied. It is calculated separately from the CQI and scored on a 0–100 scale.

**PRS Bands:**

| Band | PRS Range |
|---|---|
| Low | 0–15 |
| Moderate | 16–40 |
| High | 41–70 |
| Very High | 71–100 |

**PRS Calculation — publicly available baseline formulas:**

For tabular data:
```
BaselineRisk_tabular = 100 × p
(where p = estimated re-identification probability)
```

For data with Differential Privacy:
```
BaselineRisk_DP = min(100, 20 × ε)
(where ε = differential privacy epsilon parameter)
```

The baseline is then adjusted for data sensitivity class. MIDAS 2.0 defines sensitivity multipliers for data types (from the Lite Version Annexure I, partially public):

| Sensitivity Class | Examples | Multiplier |
|---|---|---|
| High Stigma / Personal Impact | TB, HIV, reproductive, mental-health, genomic, caste/tribe, violence | 1.5× |
| Critical / Safety-Sensitive | Forensic, detainee, conflict, tribal GPS, refugee, protest-related | 2.0× |
| Standard | General epidemiological, demographic, non-stigma health data | 1.0× |

**PRS identification risk scoring (from public snippets):**

| Scenario | Score |
|---|---|
| Names, phone numbers, IDs, GPS or full DOB still visible | 50 (Step 1 maximum) |
| Identifiers removed but unique event combinations could reveal identity | 30 |
| Only coarse info (age, sex, district, month) | 15 |
| Generalised categories (age bands, state, quarter); identities effectively hidden | 5 |

```
PRS = round(AdjustedRisk)
AdjustedRisk = BaselineRisk × SensitivityMultiplier
PRS = min(100, AdjustedRisk)
```

### 3.6 CQI × PRS Release Classification Matrix

| | PRS Low (0–15) | PRS Moderate (16–40) | PRS High (41–70) | PRS Very High (71–100) |
|---|---|---|---|---|
| **CQI Diamond / Platinum (≥85)** | Open | Controlled | Restricted | Restricted |
| **CQI Gold (70–84)** | Open | Controlled | Restricted | Restricted |
| **CQI Silver (50–69)** | Controlled | Controlled | Restricted | Restricted |
| **CQI Bronze / Remediation (<50)** | Controlled | Restricted | Restricted | Restricted |

**Special policy rule:** Clinical-genomic or high-stigma data default to Controlled unless PRS is Low with strong, independently verified Differential Privacy.

### 3.7 Expert Validation (Delphi) Process

MIDAS 2.0 is currently undergoing expert validation through a Delphi review process before wider rollout. Experts rate each domain statement on a 1–5 clarity scale. Agreement thresholds:
- Item-level CVI (I-CVI) ≥ 0.78
- Scale-level CVI (S-CVI/Ave) ≥ 0.90
- Modified Kappa (k*) ≥ 0.74 (excellent consensus)

This means the framework is **not yet fully finalised** — which is an opportunity for this toolkit to be developed in alignment with the emerging final version.

### 3.8 What Is Not Publicly Available

The following aspects of MIDAS 2.0 are not publicly accessible and must be inferred or designed independently:

| Missing Element | Approach in Toolkit |
|---|---|
| Exact sub-criteria for each 0–4 score level per domain | Reverse-engineered from domain descriptions + health data quality literature |
| Exact weights per domain (if any differential weighting exists) | Equal weighting assumed (1/15 each) unless evidence of differential weights emerges |
| Full Annexure I PRS methodology | Partially reconstructed from public snippets; clearly marked as inferred |
| Internal inter-rater reliability protocols | Not required for automated system |
| Nodal Centre verification workflows | Replaced by automated evidence-based scoring |
| Exact CQI × PRS matrix boundaries | Reconstructed from public descriptions; marked as inferred |

---

## 4. AIKosh Platform Architecture Research

### 4.1 Platform Overview

AIKosh (`aikosh.indiaai.gov.in`) is a centralised platform under the IndiaAI Mission. It serves as a national repository of datasets, models, toolkits, use cases, and a sandbox (integrated development environment). As of early 2026, it hosts 10,000+ datasets across 20 sectors with contributors including IITs, Sarvam AI, AI4Bharat, and government ministries.

### 4.2 Current Dataset Onboarding Workflow

Based on the publicly available Expression of Interest (EOI) process:

1. Organisation registers on the AIKosh platform
2. Artefact submitted with complete metadata, licensing information, and descriptive documentation
3. Submission reviewed for platform compliance, ethical alignment, and technical completeness
4. Validation through both automated and manual backend processes
5. Publication on the platform

Current automated checks are generic — format compliance, metadata completeness against AIKosh schema, licensing validation. There is **no domain-specific quality assessment** for health research datasets.

### 4.3 API & Integration Capabilities

AIKosh provides:
- API-based access for dataset retrieval and model inference
- Secure API access with authentication
- AI Sandbox with an integrated development environment
- Standardised metadata schema for submission

The platform is designed to support toolkit and artefact contributions — the EOI explicitly invites toolkits as a contribution category.

### 4.4 What AIKosh Currently Lacks

- No MIDAS-grade quality scoring for health research datasets
- No automated CQI or PRS computation at submission time
- No quality badge or certification system displayed on dataset cards
- No structured feedback to submitters on quality gaps
- No release classification (Open/Controlled/Restricted) derived from quality + privacy scores

---

## 5. Gap Analysis — MIDAS vs AIKosh

| Dimension | MIDAS 2.0 (Current) | AIKosh (Current) | Toolkit (Proposed) |
|---|---|---|---|
| Assessment type | Manual, human-in-the-loop | Generic automated metadata check | Automated MIDAS-inspired domain scoring |
| Who assesses | Dataset custodian + Nodal Centre | AIKosh backend team | Toolkit engine (automated) |
| Output | CQI + PRS + Release class | Approval / Rejection | CQI + PRS + Release class + Structured report |
| Integration | Standalone ICMR process | AIKosh-native | AIKosh-native API |
| Turnaround | Days to weeks | Hours to days | Real-time (minutes) |
| Scalability | Low — requires human reviewers | Medium | High — fully automated |
| Health data specialisation | Yes — 15 health-specific domains | No — generic checks only | Yes — 15 domains implemented |
| Privacy scoring | Yes — PRS with sensitivity classes | No | Yes — automated PRS |
| Release classification | Yes — CQI × PRS matrix | No | Yes — automated matrix |
| Audit trail | Manual documentation | Basic logging | Full automated audit log |
| GitHub / API | None | Partial (retrieval only) | Full REST API |

**Core gap:** MIDAS is the assessment philosophy. AIKosh is the platform. Nothing currently bridges them with automation. This toolkit is that bridge.

---

## 6. Problem Statement

Health research datasets submitted to AIKosh currently undergo generic metadata and compliance checks, with no mechanism to assess their scientific quality, trustworthiness, representativeness, privacy risk, or AI-readiness in a structured, evidence-based, reproducible way.

MIDAS 2.0 — ICMR's gold-standard framework for exactly this purpose — cannot be integrated into AIKosh in its current form because it is a manual, institution-facing, human-in-the-loop process with no programmatic implementation.

As a result, AIKosh's health research dataset collection grows in volume without any systematic quality intelligence, making it difficult for researchers, startups, and innovators to identify which datasets are truly ready for AI development, safe for sharing, or require improvement before use.

---

## 7. Vision Statement

Build an automated, MIDAS-inspired Dataset Quality Evaluation Toolkit that is natively integrated into AIKosh, enabling any health research dataset uploaded to the platform to receive a comprehensive, reproducible quality assessment — including a Composite Quality Index, a Privacy-Risk Score, a release classification, and an actionable structured report — without requiring manual expert review for every submission.

> MIDAS 2.0 is the assessment philosophy.  
> AIKosh is the platform.  
> This toolkit is the automation layer that bridges them.

---

## 8. Goals

1. **Automate MIDAS 2.0 assessment** — Implement all 15 quality domains as automated, deterministic scoring rules applicable to uploaded health research datasets.

2. **Produce CQI and PRS** — Compute a Composite Quality Index (0–100) and a Privacy-Risk Score (0–100) for every assessed dataset, matching MIDAS 2.0's scoring structure.

3. **Generate release classification** — Apply the CQI × PRS matrix to output an Open / Controlled / Restricted recommendation for every dataset.

4. **Integrate with AIKosh** — Expose the toolkit as an API that plugs into AIKosh's dataset submission and metadata pipeline, returning quality scores as machine-readable metadata associated with each dataset.

5. **Generate structured quality reports** — Produce a downloadable, human-readable quality assessment report per dataset including domain scores, quality band, PRS band, release recommendation, and dimension-level observations.

6. **Provide a quality dashboard** — Surface quality scores, bands, and domain breakdowns in a visual interface accessible to dataset submitters and AIKosh administrators.

7. **Support both Lite and Technical assessment modes** — The toolkit replaces both stages: an automated Lite-mode run on upload, and a deeper automated Technical-mode analysis with stricter evidence thresholds.

8. **Be fully auditable** — All scoring decisions must be explainable and traceable to specific domain criteria and data observations, producing an audit log for every assessment.

---

## 9. Non-Goals

The following are explicitly out of scope:

- **Replacing official ICMR MIDAS certification** — Toolkit scores are quality intelligence, not official ICMR certification. Formal MIDAS certification still requires ICMR Nodal Centre validation.
- **AI model training** — No ML model is trained. The toolkit is entirely rule-based and deterministic.
- **Automated dataset remediation** — The toolkit identifies quality gaps but does not automatically fix datasets.
- **Recommendation engine** — No AI-generated improvement suggestions in the initial version. Gap identification is sufficient.
- **Non-health research datasets** — The toolkit is scoped to health research datasets only, not healthcare operational data or non-health domains.
- **General-purpose data quality tool** — This is not a generic data profiler. All domains and scoring logic are specific to MIDAS 2.0's health research context.
- **Real-time streaming data assessment** — Batch/file upload only.
- **Dataset version tracking** — Not in initial scope.
- **Benchmarking across datasets** — Comparative scoring across multiple datasets is future scope.

---

## 10. Success Metrics

| Metric | Target |
|---|---|
| Domain coverage | All 15 MIDAS domains implemented and producing scores |
| CQI accuracy | CQI scores align with manually computed MIDAS scores within ±5 points on validation datasets |
| PRS accuracy | PRS scores consistent with manually estimated risk within ±10 points |
| Processing time | Full assessment completed in < 3 minutes for datasets up to 1GB |
| API availability | 99.5% uptime |
| Report completeness | 100% of reports include all 15 domain scores, CQI, PRS, band, and release class |
| AIKosh integration | Quality metadata returned as machine-readable JSON and stored with dataset record |
| Audit trail | 100% of assessments produce a full, reproducible audit log |
| False Open classification rate | < 5% of high-PRS datasets incorrectly classified as Open |

---

## 11. Stakeholders

| Stakeholder | Role | Interest |
|---|---|---|
| ICMR / MIDAS Team | Framework owner | Toolkit faithfully implements MIDAS principles; doesn't misrepresent the framework |
| IndiaAI / AIKosh Team | Platform owner | Toolkit integrates cleanly with AIKosh; quality metadata enriches dataset records |
| Health Research Institutions | Primary dataset submitters | Fast, clear feedback on dataset quality; understand what to improve |
| AI Researchers & Startups | Dataset consumers | Confidence in dataset quality before use; clear release classification |
| Dataset Custodians | Responsible for submitted data | Transparent scoring; actionable quality report |
| ICMR Nodal Centres | Validators in MIDAS process | Automated pre-assessment reduces their workload on clearly inadequate submissions |
| AIKosh Administrators | Platform operations | Reduced manual review burden; quality badge system for dataset catalog |
| Policy Makers | IndiaAI Mission oversight | Demonstrable quality assurance layer for India's health AI datasets |

---

## 12. User Personas

### Persona 1 — Dr. Priya (Health Research Dataset Custodian)
- **Who:** Epidemiologist at a regional medical institution, managing a multi-site cohort study dataset
- **Goal:** Submit dataset to AIKosh, understand its quality level, and know what improvements to make before broader sharing
- **Pain point:** MIDAS 2.0 process requires engaging a Nodal Centre and waiting weeks; no automated feedback
- **What they need:** Immediate, structured quality assessment with clear domain-level scores and gap identification

### Persona 2 — Arjun (AI Startup Developer)
- **Who:** ML engineer at a health-tech startup building a diagnostic AI model
- **Goal:** Identify which AIKosh datasets are high enough quality and sufficiently de-identified to use for model training
- **Pain point:** No quality signal on dataset cards; have to manually inspect every dataset
- **What they need:** CQI badge, PRS badge, and release classification visible on the AIKosh dataset card

### Persona 3 — AIKosh Administrator
- **Who:** IndiaAI platform team member managing dataset onboarding
- **Goal:** Efficiently process and quality-gate incoming health research dataset submissions
- **Pain point:** Manual review of every submission is slow and inconsistent
- **What they need:** Automated quality score returned on submission; ability to set quality thresholds for different release classes

### Persona 4 — ICMR Nodal Centre Reviewer
- **Who:** Expert validator responsible for formal MIDAS assessment
- **Goal:** Efficiently identify datasets that warrant formal ICMR review vs. those clearly not ready
- **What they need:** Pre-assessment quality report to triage submissions; avoid spending time on Bronze/Remediation-band datasets

---

## 13. User Stories

**As a dataset custodian (Dr. Priya), I want to:**
- Upload my health research dataset and receive an automated quality assessment within minutes
- See my domain-level scores so I understand exactly which quality dimensions are weak
- Receive a CQI and understand which performance band my dataset falls in
- Know the Privacy-Risk Score of my dataset and the recommended release classification
- Download a structured quality report to share with my institution and Nodal Centre
- Re-upload an improved dataset and see updated scores

**As an AI developer (Arjun), I want to:**
- See quality badges (CQI band, PRS band, release class) on AIKosh dataset cards
- Filter the AIKosh catalog by quality band or minimum CQI threshold
- Access the full quality report for any dataset I'm considering using
- Trust that datasets marked "Open" have been verified to have low re-identification risk

**As an AIKosh administrator, I want to:**
- Receive machine-readable quality scores via API when a dataset is submitted
- Configure minimum quality thresholds for different dataset categories
- View a dashboard showing quality distribution across the health dataset catalog
- Flag datasets below a quality threshold for follow-up without manual review

**As an ICMR reviewer, I want to:**
- Access the pre-assessment report before beginning formal MIDAS validation
- See which specific domains scored low with supporting evidence
- Use the automated report as a structured checklist for the Technical Version review

---

## 14. Proposed Solution Overview

The toolkit is an automated quality evaluation engine that:

1. **Accepts** a health research dataset upload (file + metadata form)
2. **Profiles** the dataset structure, completeness, schema, and provenance metadata
3. **Evaluates** the dataset against all 15 MIDAS domains using deterministic, automated scoring rules
4. **Computes** a CQI (domain scores summed and normalised to 0–100)
5. **Computes** a PRS (re-identification risk baseline + sensitivity adjustment)
6. **Classifies** the dataset release level using the CQI × PRS matrix
7. **Generates** a structured quality report (JSON + PDF/HTML)
8. **Returns** machine-readable quality metadata to AIKosh via REST API
9. **Stores** the assessment with a full audit log

The toolkit is a **rule-based, deterministic scoring engine** — not a machine learning model. Every score is explainable and traceable to specific domain criteria and data observations. This makes scores auditable and defensible in a government/research context.

---

## 15. Functional Scope

### In Scope

| Feature | Description |
|---|---|
| Dataset upload | CSV, JSON, XLSX, Parquet, FHIR JSON, DICOM manifest, ZIP |
| Metadata intake form | Structured form collecting domain-relevant metadata not inferable from file alone |
| Dataset profiling | Schema inference, completeness analysis, statistical summary, duplicate detection |
| 15-domain quality assessment | Automated scoring of all 15 MIDAS domains |
| CQI computation | Formula-based composite score normalised to 0–100 |
| PRS computation | Re-identification risk score with sensitivity class adjustment |
| Release classification | Open / Controlled / Restricted based on CQI × PRS matrix |
| Quality report generation | Structured JSON report + rendered HTML/PDF output |
| Quality dashboard | Domain-level radar chart, score history, band visualisation |
| AIKosh API integration | REST API returning quality metadata to AIKosh dataset record |
| Audit log | Full, reproducible record of every assessment decision |
| Re-assessment | Ability to re-run assessment on updated dataset version |

### Out of Scope (Current Version)

- Automated dataset remediation
- AI-generated improvement recommendations
- Dataset version control / diff tracking
- Cross-dataset comparison and benchmarking
- Real-time streaming assessment
- Non-health research dataset support
- Official ICMR MIDAS certification issuance

---

## 16. End-to-End User Journey

```
[Dataset Custodian]
       |
       | 1. Upload dataset file + fill metadata form
       ↓
[Upload & Ingestion Module]
       |
       | 2. Parse, validate format, extract schema
       ↓
[Dataset Profiling Engine]
       |
       | 3. Generate dataset profile (completeness, schema, stats, duplicates)
       ↓
[Quality Assessment Engine]
       |
       | 4. Score each of 15 MIDAS domains (0–4)
       ↓
[CQI Engine]           [PRS Engine]
       |                      |
       | 5a. Compute CQI      | 5b. Compute PRS
       ↓                      ↓
[Release Classification Engine]
       |
       | 6. Apply CQI × PRS matrix → Open / Controlled / Restricted
       ↓
[Report Generation Module]
       |
       | 7. Generate structured JSON report + HTML/PDF
       ↓
[AIKosh Integration Layer]
       |
       | 8. POST quality metadata to AIKosh dataset record via API
       ↓
[Dashboard]
       |
       | 9. Custodian views domain scores, CQI, PRS, release class, report
       ↓
[Audit Log]
       |
       | 10. Full assessment stored with reproducible trace
```

---

## 17. Module Specifications

### 17.1 Dataset Upload & Ingestion Module

**Purpose:** Accept dataset metadata submissions containing S3 storage keys, validate file details, and pass references to the profiling engine.

**Inputs:**
- Dataset file S3 key (uploaded directly by client to AWS S3 via secure temporary pre-signed URL)
- Metadata intake form (structured JSON payload covering fields required for domains not inferable from data alone)
- Optional: data dictionary, SOPs, consent documentation S3 keys (uploaded as attachments via pre-signed URLs)

**Metadata Intake Form Fields (required for scoring):**

| Field | Required For Domain |
|---|---|
| Dataset name and version | 2, 3, 15 |
| Dataset type (tabular / imaging / text / multimodal) | 5, 6 |
| Health research study type (RCT / cohort / cross-sectional / registry / etc.) | 1, 4 |
| Target population description | 4 |
| Geographic coverage (districts / states / national) | 4 |
| Age range and sex distribution of subjects | 4 |
| Number of sites contributing data | 4 |
| Data collection period (start–end dates) | 3, 9 |
| Annotation methodology (if applicable) | 1 |
| Number of annotators and inter-rater reliability method | 1 |
| Standards used (FHIR / HL7 / SNOMED / ICD / custom) | 5 |
| Ethics approval status and IRB/IEC reference | 10 |
| Consent type (individual / waiver / community) | 7, 10 |
| De-identification method applied | 7 |
| Differential Privacy epsilon (if applicable) | 7, PRS |
| Data sensitivity class (standard / high stigma / critical) | PRS |
| Persistent identifier (DOI / accession number) | 2 |
| License type | 8, 12 |
| Synthetic data percentage (if any) | 11 |
| Storage location and access control method | 8 |
| Linked model identifiers (if any) | 13 |
| Data dictionary availability | 3 |
| Provenance pipeline availability | 9 |

**Validation:**
- File format and size validation (enforced by frontend before S3 upload, and verified by profiling engine upon reading from S3)
- Schema extraction (done by profiling engine)
- Encoding detection (done by profiling engine)
- Duplicate record detection (hash-based, done by profiling engine)

**Outputs:** S3 key references and metadata JSON registered in PostgreSQL and passed to the profiling task.

---

### 17.2 Dataset Profiling Engine

**Purpose:** Generate a comprehensive statistical and structural profile of the dataset to feed into domain scoring.

**Profile Components:**

| Component | Details |
|---|---|
| Row / column count | Total records and features |
| Column-level completeness | Missing value % per column |
| Data type inference | Numeric, categorical, date, free text, binary |
| Value distribution summary | Mean, median, std, min, max per numeric column |
| Categorical cardinality | Unique value counts per categorical column |
| Duplicate row detection | Exact and near-duplicate % |
| Schema consistency | Are all records conformant to the inferred schema? |
| Outlier detection | Statistical outlier % per numeric column (IQR method) |
| Identifier presence detection | Heuristic check for name-like, phone-like, ID-like columns |
| Date range extraction | Earliest and latest dates in temporal columns |
| Encoding quality | UTF-8 compliance, character anomalies |
| File-level metadata extraction | File size, format, hash (SHA-256) |

**Output:** Dataset Profile JSON — referenced by all 15 domain scoring modules.

---

### 17.3 Quality Assessment Engine (15 Domains)

**Purpose:** Score each of the 15 MIDAS domains on a 0–4 scale using automated rules derived from the dataset profile and metadata form.

Each domain scorer is an independent module. All 15 run in parallel. Each produces:
- A score (0–4)
- A scoring rationale string (one per criterion checked)
- A list of evidence items that supported the score
- A list of gaps that prevented a higher score
- A confidence level (High / Medium / Low) indicating how much of the scoring was based on direct data observation vs. metadata form responses

**Note:** Domains 1, 4, 9, 10, and 12 are partially dependent on metadata form responses (evidence that cannot be inferred from the file alone). The confidence level field distinguishes direct-observation scoring from metadata-form-reliant scoring.

See Section 18 for the full domain-by-domain automated metric specification.

---

### 17.4 CQI Calculation Engine

**Purpose:** Aggregate the 15 domain scores into a single Composite Quality Index.

**Logic:**
```python
def compute_cqi(domain_scores: dict, domain_11_applicable: bool) -> float:
    total_score = sum(domain_scores.values())
    max_possible = 60 if domain_11_applicable else 56
    cqi = (total_score / max_possible) * 100
    return round(cqi, 1)

def get_cqi_band(cqi: float) -> str:
    if cqi >= 95:   return "Diamond"
    if cqi >= 85:   return "Platinum"
    if cqi >= 70:   return "Gold"
    if cqi >= 50:   return "Silver"
    if cqi >= 25:   return "Bronze"
    return "Remediation"
```

**Output:** CQI value (0–100, 1 decimal), CQI band, domain score breakdown.

---

### 17.5 PRS Calculation Engine

**Purpose:** Compute the Privacy-Risk Score based on re-identification risk and sensitivity class.

**Inputs from dataset profile and metadata form:**
- De-identification method applied
- Presence of direct identifiers (from profiler's heuristic scan)
- Remaining quasi-identifiers (age, sex, location granularity, date granularity)
- Differential Privacy epsilon (if applicable)
- Sensitivity class (standard / high stigma / critical)

**Logic:**
```python
def compute_baseline_risk(deidentification_info: dict, profile: dict) -> float:
    if profile["direct_identifiers_detected"]:
        return 50.0  # Maximum Step 1 score — identifiers present
    
    location_granularity = deidentification_info["location_granularity"]
    temporal_granularity = deidentification_info["temporal_granularity"]
    
    if location_granularity == "village" and profile["rare_condition"]:
        return 30.0
    if location_granularity in ["district", "month"]:
        return 15.0
    if location_granularity in ["state", "region"]:
        return 5.0
    
    # Differential Privacy path
    if deidentification_info.get("differential_privacy_applied"):
        epsilon = deidentification_info["epsilon"]
        return min(100, 20 * epsilon)
    
    return 15.0  # Default moderate

SENSITIVITY_MULTIPLIERS = {
    "standard": 1.0,
    "high_stigma": 1.5,   # TB, HIV, mental health, genomic, etc.
    "critical": 2.0        # Forensic, conflict, detainee, refugee, etc.
}

def compute_prs(baseline_risk: float, sensitivity_class: str) -> int:
    multiplier = SENSITIVITY_MULTIPLIERS.get(sensitivity_class, 1.0)
    adjusted = baseline_risk * multiplier
    return min(100, round(adjusted))

def get_prs_band(prs: int) -> str:
    if prs <= 15:   return "Low"
    if prs <= 40:   return "Moderate"
    if prs <= 70:   return "High"
    return "Very High"
```

**Output:** PRS value (0–100, integer), PRS band.

---

### 17.6 Release Classification Engine

**Purpose:** Apply the CQI × PRS matrix to determine dataset release classification.

**Logic:**
```python
def classify_release(cqi: float, prs: int, sensitivity_class: str) -> str:
    prs_band = get_prs_band(prs)
    cqi_band = get_cqi_band(cqi)
    
    # Special policy override
    if sensitivity_class in ["high_stigma", "critical"]:
        if prs_band != "Low":
            return "Restricted"
        # Even with Low PRS, high-stigma defaults to Controlled
        # unless Differential Privacy is verified
        return "Controlled"
    
    # Standard matrix
    if cqi >= 70 and prs_band == "Low":
        return "Open"
    if cqi >= 70 and prs_band == "Moderate":
        return "Controlled"
    if prs_band in ["High", "Very High"]:
        return "Restricted"
    if cqi < 50:
        return "Controlled" if prs_band == "Low" else "Restricted"
    
    return "Controlled"
```

**Output:** Release classification (Open / Controlled / Restricted) with justification string.

---

### 17.7 Report Generation Module

**Purpose:** Generate a structured assessment report in multiple formats.

**Report Contents:**
- Assessment metadata (dataset name, submission date, assessment ID, toolkit version)
- Dataset profile summary
- Domain-by-domain scores (0–4) with rationale and evidence
- CQI value, band, and formula trace
- PRS value, band, and computation trace
- Release classification and justification
- Quality gap summary (domains scoring 0–2)
- Strengths summary (domains scoring 3–4)
- Audit log reference

**Output Formats:**
- Structured JSON (primary — consumed by AIKosh API)
- HTML report (human-readable, self-contained)
- PDF (generated from HTML)

---

### 17.8 Dashboard & Visualisations
 
 **Purpose:** Provide a visual interface for custodians and administrators to review assessment results.
 
 **Dashboard Elements:**
 - **Radar / Spider Chart:** 15-domain score visualisation
 - **CQI Gauge:** 0–100 gauge with band colour coding
 - **PRS Gauge:** 0–100 gauge with band colour coding
 - **Release Class Badge:** Open (green) / Controlled (amber) / Restricted (red)
 - **Domain Score Table:** All 15 domains with score, max, rationale, confidence level
 - **Gap Identification Panel:** Domains below 2, sorted by score ascending
 - **Score History:** CQI and PRS trend across assessment versions (for re-assessments)
 - **Transparent Failure Panel:** If the background evaluation job fails (reaches `failed` status), the dashboard must display a clear, human-readable description of the error and traceback to the user for transparent debugging and self-correction (e.g., file parse failures, format mismatches, or missing parameters).

---

### 17.9 AIKosh Integration Layer

**Purpose:** Return quality metadata to AIKosh's dataset record system via REST API.

**Integration Pattern:**
- Toolkit exposes a REST API endpoint
- AIKosh calls the endpoint at dataset submission time with dataset file + metadata
- Toolkit runs assessment asynchronously and POSTs results back to a AIKosh webhook
- AIKosh stores quality metadata as structured fields on the dataset record
- Quality badges (CQI band, PRS band, release class) rendered on dataset catalog card

**Quality Metadata Schema returned to AIKosh:**
```json
{
  "assessment_id": "uuid",
  "dataset_id": "aikosh_dataset_id",
  "assessed_at": "ISO8601 timestamp",
  "toolkit_version": "1.0.0",
  "cqi": 74.2,
  "cqi_band": "Gold",
  "prs": 12,
  "prs_band": "Low",
  "release_classification": "Open",
  "domain_scores": {
    "annotation_labelling_reliability": 3,
    "metadata_completeness": 4,
    "documentation_user_guidance": 3,
    "population_representativeness": 2,
    "data_structure_interoperability": 3,
    "ai_analytics_readiness": 3,
    "privacy_identifiability": 4,
    "security_access_governance": 3,
    "provenance_workflow_transparency": 2,
    "ethical_social_accountability": 3,
    "synthetic_simulated_data": null,
    "stewardship_governance": 3,
    "model_linkage_integrity": 1,
    "environmental_sustainability": 2,
    "continuous_curation_feedback": 2
  },
  "domain_11_applicable": false,
  "report_url": "https://toolkit.aikosh.gov.in/reports/uuid",
  "audit_log_id": "uuid"
}
```

---

## 18. Quality Assessment Framework Specification

This section defines how the toolkit scores each of the 15 MIDAS 2.0 domains using automated, deterministic rules.

**Scoring sources:**
- `[DATA]` — Directly inferred from uploaded dataset file via profiler
- `[META]` — Sourced from metadata intake form (requires custodian input)
- `[INFERRED]` — Marked as assumption where MIDAS public sources are insufficient

### 18.1 Domain 1 — Annotation / Labelling Reliability

**What it measures:** Quality and reliability of labels/annotations produced by experts or trained readers.

| Score | Criteria (All must be true) | Source |
|---|---|---|
| 0 | No annotation present or no information provided | DATA, META |
| 1 | Annotations exist but no annotator qualification, no protocol, no IRR metric | META |
| 2 | Annotators qualified, protocol documented, but no IRR metric or < 0.6 Kappa | META |
| 3 | Qualified annotators, documented protocol, IRR ≥ 0.6, adjudication process described | META |
| 4 | All of Score 3 + IRR ≥ 0.8 (Cohen's Kappa or equivalent), ≥ 2 independent annotators, gold standard reference available | META |

**Automated checks:**
- If dataset has label/annotation columns → flag for annotation scoring
- If no label columns → score based on metadata form response about annotation methodology
- Extract IRR metric if provided in metadata form
- Flag if inter-rater reliability not reported

**INFERRED:** Exact Kappa thresholds (0.6 / 0.8) derived from standard health informatics literature, not explicitly stated in MIDAS 2.0 public docs.

---

### 18.2 Domain 2 — Metadata Completeness

**What it measures:** Rich, machine-actionable metadata with persistent identifiers to enable discovery and reuse.

| Score | Criteria (All must be true) | Source |
|---|---|---|
| 0 | No metadata provided beyond file name | META |
| 1 | Basic metadata (name, description) but no standards, no persistent identifier | META |
| 2 | Structured metadata present, some standard fields, no persistent identifier | META |
| 3 | Metadata follows a recognised schema (DataCite, schema.org, DCAT), persistent identifier (DOI/accession) present | META |
| 4 | All of Score 3 + machine-actionable, versioned metadata, linked to study registry, all mandatory fields complete | META |

**Automated checks:**
- Validate DOI/accession number format if provided
- Check metadata field completeness against AIKosh required schema
- Check for linked study registry (ClinicalTrials.gov, CTRI, etc.)

---

### 18.3 Domain 3 — Documentation & User Guidance

**What it measures:** Clarity and depth of human-readable documentation for context, methods, and reuse.

| Score | Criteria | Source |
|---|---|---|
| 0 | No documentation provided | META |
| 1 | Minimal description only, no data dictionary, no usage guidance | META |
| 2 | README or description present, partial data dictionary | META |
| 3 | Full data dictionary, collection methodology described, known limitations documented | META |
| 4 | All of Score 3 + reuse guidance, example code/queries, changelog, contact for queries | META |

**Automated checks:**
- Check if data dictionary file uploaded
- Check if README/description meets minimum word count threshold
- Detect column names in dataset and verify they appear in data dictionary (if provided)

---

### 18.4 Domain 4 — Population Representativeness

**What it measures:** How well the dataset reflects the intended population across sites, regions, age, sex, and other axes.

| Score | Criteria | Source |
|---|---|---|
| 0 | No population description provided | META |
| 1 | Single site, narrow demographic, no representativeness analysis | META, DATA |
| 2 | Multi-site or described target population, but obvious gaps (age range narrow, single sex, single region) | META, DATA |
| 3 | Multi-site, multi-region, documented sampling strategy, age and sex distribution reported | META, DATA |
| 4 | All of Score 3 + formal representativeness analysis against population census/survey, socioeconomic and geographic diversity documented | META |

**Automated checks:**
- If dataset contains age/sex columns → compute distribution and flag imbalance
- Check number of sites from metadata form
- Check geographic spread from metadata form

---

### 18.5 Domain 5 — Data Structure & Interoperability

**What it measures:** Mapping to healthcare standards and automated data-quality checks: conformance, completeness, plausibility.

| Score | Criteria | Source |
|---|---|---|
| 0 | Custom schema, no standard, no data quality checks | DATA, META |
| 1 | Standard mentioned but not actually applied; no automated DQ checks | META |
| 2 | Partial standard mapping (e.g., some ICD codes present but inconsistent), basic completeness check | DATA, META |
| 3 | Full standard applied (FHIR, HL7, SNOMED, ICD-10+), conformance verified, completeness ≥ 90% on key fields | DATA, META |
| 4 | All of Score 3 + plausibility checks passed (value ranges, referential integrity), machine-readable data dictionary aligned to ontology | DATA, META |

**Automated checks:**
- `[DATA]` Detect standard code patterns (ICD codes, SNOMED codes, LOINC codes) in categorical columns
- `[DATA]` Compute column completeness % across all columns
- `[DATA]` Check for value range violations (e.g., age < 0, BMI > 100) in numeric columns
- `[DATA]` Check referential integrity across related columns
- `[META]` Verify declared standard against detected coding patterns

---

### 18.6 Domain 6 — AI / Analytics Readiness

**What it measures:** Packaging for benchmarking and safeguards against data leakage and distribution shift.

| Score | Criteria | Source |
|---|---|---|
| 0 | Raw data dump, no splits, no class balance information, no feature documentation | DATA, META |
| 1 | Basic label/target column present, but no train/test split, no class balance analysis | DATA |
| 2 | Train/test split defined, class distribution reported but imbalance not addressed | DATA, META |
| 3 | Pre-defined splits, class balance documented and addressed (oversampling/undersampling noted), known distribution shift risks described | DATA, META |
| 4 | All of Score 3 + benchmark baseline provided, feature importance or correlation matrix available, data leakage prevention documented | DATA, META |

**Automated checks:**
- `[DATA]` Detect label/target column (binary, multiclass, regression target)
- `[DATA]` Compute class distribution and imbalance ratio
- `[DATA]` Check for train/test split indicators (column named "split", "fold", "partition")
- `[DATA]` Run inter-feature correlation analysis to flag potential leakage signals

---

### 18.7 Domain 7 — Privacy & Identifiability

**What it measures:** Risk that individuals can be re-identified or sensitive attributes can be inferred.

| Score | Criteria | Source |
|---|---|---|
| 0 | Direct identifiers present (names, phone numbers, full DOB, GPS coordinates) | DATA, META |
| 1 | Direct identifiers removed but indirect quasi-identifiers at high granularity (village + rare disease + date) | DATA, META |
| 2 | Quasi-identifiers generalised but re-identification risk still moderate; no formal de-identification methodology documented | DATA, META |
| 3 | Formal de-identification applied (method documented), quasi-identifiers generalised to safe granularity, no direct identifiers | META |
| 4 | All of Score 3 + Differential Privacy applied with documented epsilon, or k-anonymity ≥ 5 formally verified | META |

**Automated checks:**
- `[DATA]` Heuristic scan for name-like columns (string columns with high cardinality + name-pattern regex)
- `[DATA]` Scan for phone number patterns, email patterns, national ID patterns
- `[DATA]` Detect GPS coordinate columns (lat/long numeric pairs)
- `[DATA]` Flag columns containing full date of birth (DOB with day precision)
- `[META]` Check declared de-identification method

---

### 18.8 Domain 8 — Security & Access Governance

**What it measures:** Demonstrable operational security and auditability of access to data and systems.

| Score | Criteria | Source |
|---|---|---|
| 0 | No access control, publicly downloadable with no controls | META |
| 1 | Basic access control (login required) but no formal policy, no audit log | META |
| 2 | Formal access policy exists, access logs maintained, but no DUA or user verification | META |
| 3 | Documented DUA (Data Use Agreement), user verification, access request process, audit trail | META |
| 4 | All of Score 3 + encryption at rest and in transit, penetration testing or security audit completed, incident response plan | META |

**Automated checks:** Primarily metadata-form-driven. Verify consistency between declared access controls and platform-level settings.

---

### 18.9 Domain 9 — Provenance & Workflow Transparency

**What it measures:** End-to-end trace from raw data to release, with executable pipelines.

| Score | Criteria | Source |
|---|---|---|
| 0 | No provenance information | META |
| 1 | Basic description of data source but no processing pipeline | META |
| 2 | Processing steps described in narrative form but not executable | META |
| 3 | Documented pipeline with version-controlled scripts, raw-to-release trace | META |
| 4 | All of Score 3 + fully executable and reproducible pipeline (Docker, Git, Makefile), outputs are hash-verifiable | META |

**Automated checks:**
- Check if pipeline script files uploaded (`.py`, `.R`, `.sh`, `Makefile`, `Dockerfile`)
- Check if GitHub/GitLab repository URL provided in metadata

---

### 18.10 Domain 10 — Ethical & Social Accountability

**What it measures:** Processes for equity impact, stakeholder engagement, and redressal.

| Score | Criteria | Source |
|---|---|---|
| 0 | No ethics approval, no consent documentation | META |
| 1 | Ethics approval obtained but no consent documentation, no equity considerations | META |
| 2 | Ethics approval + informed consent documented, but no bias/equity analysis | META |
| 3 | Ethics approval, consent, documented equity analysis (age/sex/geographic bias check) | META |
| 4 | All of Score 3 + community/stakeholder engagement documented, redressal mechanism exists, equity impact formally assessed | META |

**Automated checks:**
- `[META]` Verify ethics approval reference number format
- `[DATA]` If demographic columns present, run demographic parity check and flag representation gaps

---

### 18.11 Domain 11 — Synthetic / Simulated Data *(if applicable)*

**What it measures:** Utility and privacy of synthetic data relative to real data.

*This domain scores N/A and is excluded from the CQI denominator if the dataset contains no synthetic or simulated data.*

| Score | Criteria | Source |
|---|---|---|
| 0 | Synthetic data present but no utility evaluation, no privacy analysis | META |
| 1 | Basic utility metrics reported but significantly below real data; no privacy analysis | META |
| 2 | Utility evaluated (e.g., similarity metrics) but privacy not formally tested | META |
| 3 | Utility and privacy both evaluated (membership inference, attribute inference tests), results documented | META |
| 4 | All of Score 3 + results comparable to real data on key metrics, synthetic data generation method documented and reproducible | META |

**Automated checks:**
- `[META]` Flag if synthetic data percentage > 0%
- `[DATA]` If synthetic data present, check for utility comparison statistics in metadata

---

### 18.12 Domain 12 — Stewardship & Governance

**What it measures:** Organisational readiness and compliance for responsible data stewardship.

| Score | Criteria | Source |
|---|---|---|
| 0 | No governance structure, no named data steward | META |
| 1 | Named data steward exists but no formal governance policy | META |
| 2 | Governance policy exists but not formally implemented or audited | META |
| 3 | Formal governance policy, named responsible parties, compliance with applicable regulations (DPDP Act) | META |
| 4 | All of Score 3 + periodic governance audits, stewardship continuity plan, defined data lifecycle and retention policy | META |

**Automated checks:** Entirely metadata-form-driven.

---

### 18.13 Domain 13 — Model Linkage Integrity

**What it measures:** Traceable and verifiable linkages between datasets and any released models.

| Score | Criteria | Source |
|---|---|---|
| 0 | No linked models, or models exist but no linkage documented | META |
| 1 | Linked models mentioned but no versioning or reproducibility information | META |
| 2 | Model identifiers provided, basic training documentation | META |
| 3 | Model version pinned to dataset version, training code available | META |
| 4 | All of Score 3 + model card published, training pipeline reproducible, evaluation results documented with dataset version reference | META |

**Automated checks:**
- `[META]` Verify model identifiers if provided (AIKosh model IDs, HuggingFace IDs, etc.)
- Score 0 if no linked models and no model linkage information provided (not penalised if no models exist — score 3 assumed if dataset is not model-linked)

**INFERRED:** MIDAS public description mentions model linkage as a domain but does not specify whether absence of model links is penalised. We assume neutral (score 3) if the dataset is genuinely not linked to any model.

---

### 18.14 Domain 14 — Environmental Sustainability

**What it measures:** Measurement and management of energy and carbon footprints from storage and compute.

| Score | Criteria | Source |
|---|---|---|
| 0 | No sustainability information | META |
| 1 | Awareness mentioned but no measurement | META |
| 2 | Energy or compute usage estimated | META |
| 3 | Carbon footprint estimated, storage optimisation applied (compression, deduplication) | META, DATA |
| 4 | All of Score 3 + certified green compute infrastructure, offset or reduction plan documented | META |

**Automated checks:**
- `[DATA]` Measure compressed file size vs. uncompressed (compression ratio as proxy for storage efficiency)
- `[META]` Check if sustainability information provided

**INFERRED:** This is an emerging domain in health data quality frameworks. Scoring criteria derived from MIDAS description + general sustainability reporting standards.

---

### 18.15 Domain 15 — Continuous Curation & Feedback

**What it measures:** Release cadence, user feedback integration, and versioning discipline.

| Score | Criteria | Source |
|---|---|---|
| 0 | Single release, no versioning, no feedback mechanism | META |
| 1 | Version number present but no changelog, no feedback channel | META |
| 2 | Changelog exists, basic version history, no formal feedback integration | META |
| 3 | Semantic versioning, documented changelog, user feedback mechanism exists | META |
| 4 | All of Score 3 + demonstrated feedback-driven updates (issues resolved and reflected in new versions), scheduled re-assessment plan | META |

**Automated checks:**
- `[META]` Check version field format (semantic vs. arbitrary)
- `[META]` Check if changelog provided
- `[DATA]` Compare submission against any prior version on file (if re-assessment)

---

### 18.6 Assumptions & Inferences Made

All assumptions are clearly flagged in assessment reports.

| Domain | Assumption | Basis |
|---|---|---|
| All | Equal weighting (1/15) across domains | MIDAS public docs do not specify differential domain weights |
| 1 | Kappa ≥ 0.6 / ≥ 0.8 thresholds | Standard health informatics inter-rater reliability literature |
| 5 | Column completeness ≥ 90% for Score 3 | WHO and FHIR data quality guidelines |
| 13 | Neutral score (3) when no models linked | MIDAS domain description implies linkage when models exist |
| 14 | Compression ratio as sustainability proxy | Derived from storage efficiency literature |
| CQI×PRS | Full release matrix | Reconstructed from MIDAS homepage description |
| PRS | Sensitivity multipliers (1.0×, 1.5×, 2.0×) | Directly from MIDAS Lite Version Annexure I (public snippets) |

---

## 19. API Requirements

### Core Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/auth/register` | POST | Register new user account |
| `/api/v1/auth/login` | POST | Login and receive HttpOnly session cookie |
| `/api/v1/auth/logout` | POST | Clear session cookie |
| `/api/v1/auth/me` | GET | Get current user profile |
| `/api/v1/auth/keys` | GET | List active API keys for current user |
| `/api/v1/auth/keys` | POST | Generate new developer API key |
| `/api/v1/auth/keys/{key_id}` | DELETE | Revoke API key |
| `/api/v1/admin/users` | GET | List all users (admin only) |
| `/api/v1/admin/users/{id}/toggle-active` | POST | Suspend/reactivate user (admin only) |
| `/api/v1/assess/upload-url` | POST | Request pre-signed S3 upload URL |
| `/api/v1/assess` | POST | Submit dataset metadata + S3 file key for assessment |
| `/api/v1/assess/{assessment_id}` | GET | Get assessment status and results |
| `/api/v1/assess/{assessment_id}/report` | GET | Download full quality report (JSON / HTML / PDF) |
| `/api/v1/assess/{assessment_id}/audit` | GET | Retrieve full audit log |
| `/api/v1/datasets/{dataset_id}/assessments` | GET | List all assessments for a dataset |
| `/api/v1/health` | GET | Health check |

### Authentication
- **Dual Authentication Model:**
  - **User Session Auth:** Secure `HttpOnly` cookie-based JWT session for browser human logins (Sign-Up / Sign-In / Log-Out pages on the React UI).
  - **Developer API Key Auth:** Header-based API Key (`Authorization: Bearer <key>`) for programmatic integration and automated scripts.
- **Admin Access Boundaries:** Admin users can list and manage user accounts but cannot view or download user datasets or access sensitive assessment reports.

### Async Pattern
- `/api/v1/assess` returns immediately with `assessment_id` and `status: processing`
- Client polls `/api/v1/assess/{assessment_id}` or receives webhook callback when complete
- Typical processing time < 3 minutes for datasets ≤ 1GB

### AIKosh Webhook
- Toolkit POSTs quality metadata JSON to AIKosh-provided webhook URL on completion
- Includes `dataset_id` for AIKosh to associate results with the dataset record

---

## 20. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        AIKosh Platform                       │
│              (Dataset Submission & Catalog)                  │
└────────────────────────┬────────────────────────────────────┘
                         │ API call on dataset submission
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              AIKosh Dataset Quality Toolkit                  │
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌───────────────┐  │
│  │   Upload &   │───▶│   Dataset    │───▶│    Quality    │  │
│  │  Ingestion   │    │   Profiler   │    │  Assessment   │  │
│  │   Module     │    │   Engine     │    │  Engine (×15) │  │
│  └──────────────┘    └──────────────┘    └───────┬───────┘  │
│                                                  │           │
│                         ┌────────────────────────┤           │
│                         ▼                        ▼           │
│                  ┌─────────────┐         ┌─────────────┐    │
│                  │  CQI Engine │         │  PRS Engine │    │
│                  └──────┬──────┘         └──────┬──────┘    │
│                         └──────────┬────────────┘           │
│                                    ▼                         │
│                         ┌──────────────────┐                │
│                         │    Release       │                 │
│                         │  Classification  │                 │
│                         │     Engine       │                 │
│                         └────────┬─────────┘                │
│                                  ▼                           │
│                    ┌─────────────────────────┐              │
│                    │   Report Generation     │              │
│                    │   (JSON + HTML + PDF)   │              │
│                    └────────────┬────────────┘              │
│                                 │                            │
│   ┌─────────────┐               │   ┌───────────────────┐   │
│   │  Dashboard  │◀──────────────┴──▶│  AIKosh           │   │
│   │     UI      │                   │  Integration Layer │   │
│   └─────────────┘                   └───────────────────┘   │
│                                                              │
│   ┌──────────────────────────────────────────────────────┐  │
│   │                    Audit Log Store                    │  │
│   └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Technology Stack:**

| Layer | Technology |
|---|---|
| API | FastAPI (Python) |
| Frontend | Next.js 14 (App Router) + TypeScript |
| Styling | Tailwind CSS + shadcn/ui |
| Data Fetching | TanStack Query v5 |
| Forms | React Hook Form + Zod |
| Global State | Zustand |
| Profiling | pandas 2.2 + pyarrow |
| Scoring Engine | Python (pure rule-based, no ML dependencies) |
| Report Generation | Jinja2 (HTML) + WeasyPrint (PDF) |
| Database | PostgreSQL 16 |
| Object Storage | AWS S3 Object Storage |
| Task Queue | Celery + Redis |
| Charts | Recharts |
| Deployment | Docker + Kubernetes |

---

## 21. Data Flow

1. **Upload:** Client requests a pre-signed S3 upload URL, uploads the dataset file directly to MinIO/S3, and submits the metadata form containing the S3 file key to FastAPI.
2. **Validation:** Format check, size check, encoding check verified by the backend profiling task → fail assessment if invalid.
3. **Storage:** File stored in secure object storage (encrypted at rest).
4. **Profiling:** Profiling engine reads file from S3, generates Dataset Profile JSON.
5. **Assessment:** 15 domain scorers run in parallel against Profile JSON + metadata form.
6. **Aggregation:** CQI engine aggregates domain scores; PRS engine computes privacy risk.
7. **Classification:** Release classification engine applies matrix.
8. **Report:** Report generator produces JSON report + renders HTML/PDF.
9. **Integration:** Quality metadata POSTed to AIKosh webhook.
10. **Storage:** Assessment record + report + audit log persisted in PostgreSQL and object storage.
11. **Cleanup:** Dataset file retained in object storage until manually deleted by the user via the UI/API.

---

## 22. Database Design Overview

### Core Tables

**users** *(root entity — all other records cascade from here)*
```
id (UUID, PK)
email (VARCHAR, UNIQUE)
hashed_password (VARCHAR)
role (ENUM: user/reviewer/admin)
is_active (BOOLEAN)
created_at (TIMESTAMPTZ)
```

**api_keys** *(developer keys, FK → users)*
```
key_id (UUID, PK)
key_hash (VARCHAR, UNIQUE) — SHA-256 hash only; raw key never stored
key_prefix (VARCHAR) — first 8 chars for display
user_id (UUID, FK → users.id)
is_active (BOOLEAN)
created_at / last_used_at / expires_at (TIMESTAMPTZ)
```

**assessments** *(FK → users + api_keys)*
```
assessment_id (UUID, PK)
dataset_id (VARCHAR) — AIKosh dataset identifier
user_id (UUID, FK → users.id)
api_key_id (UUID, FK → api_keys.key_id, nullable)
submission_timestamp (TIMESTAMPTZ)
completion_timestamp (TIMESTAMPTZ)
status (ENUM: queued / processing / complete / failed)
toolkit_version (VARCHAR)
domain_11_applicable (BOOLEAN)
s3_file_key (VARCHAR)
error_message (TEXT)
error_traceback (TEXT)
celery_task_id (VARCHAR)
```

**domain_scores**
```
score_id (UUID, PK)
assessment_id (UUID, FK)
domain_number (INT 1–15)
domain_name (VARCHAR)
score (INT 0–4)
rationale (TEXT)
evidence_items (JSONB)
gaps (JSONB)
confidence_level (ENUM: High / Medium / Low)
```

**assessment_results**
```
result_id (UUID, PK)
assessment_id (UUID, FK)
cqi (DECIMAL)
cqi_band (VARCHAR)
prs (INT)
prs_band (VARCHAR)
release_classification (ENUM: Open / Controlled / Restricted)
classification_justification (TEXT)
report_url (VARCHAR)
```

**audit_logs** *(append-only — enforced by PostgreSQL rule)*
```
log_id (UUID, PK)
assessment_id (UUID, FK)
event_type (VARCHAR)
event_timestamp (TIMESTAMPTZ)
event_detail (JSONB)
component (VARCHAR)
severity (ENUM: INFO / WARNING / ERROR)
```

---

## 23. Supported Dataset Formats

| Format | Extension | Notes |
|---|---|---|
| Comma-Separated Values | .csv | Primary tabular format |
| Excel | .xlsx | Converted to tabular on ingest |
| JSON | .json | Structured records or FHIR bundles |
| Parquet | .parquet | Columnar format for large datasets |
| FHIR JSON | .json (FHIR Bundle) | Detected by schema pattern |
| DICOM Manifest | .csv / .json | Manifest listing DICOM files + metadata |
| ZIP Archive | .zip | Extracted and profiled recursively |
| Tab-Separated Values | .tsv | Same pipeline as CSV |

**Maximum file size:** 5GB (configurable)
**Encoding:** UTF-8 required; auto-detection for common alternatives (ISO-8859-1, UTF-16) with conversion

---

## 24. Non-Functional Requirements

| Requirement | Target |
|---|---|
| **Performance** | Full assessment < 3 minutes for datasets ≤ 1GB |
| **Scalability** | Handle 100 concurrent assessment jobs |
| **Availability** | 99.5% uptime (excluding planned maintenance) |
| **Latency** | API response to submission < 2 seconds (async job initiated) |
| **Data retention** | Assessment results retained for 5 years minimum |
| **Reproducibility** | Same dataset + same metadata → identical scores (deterministic) |
| **Audit completeness** | 100% of scoring decisions traceable in audit log |
| **Internationalisation** | Reports available in English; Hindi support in future roadmap |

---

## 25. Security & Privacy Requirements

| Requirement | Implementation |
|---|---|
| Encryption at rest | AES-256 for all stored files and reports |
| Encryption in transit | TLS 1.3 minimum on all API endpoints |
| Dataset isolation | Each dataset processed in isolated execution context |
| Dataset deletion | Dataset files and reports retained until manually deleted by the user via UI/API |
| Secure data storage | Raw dataset content stored in private S3/MinIO bucket under strict tenant isolation; only accessible to the submitter |
| Access control | Role-based (submitter / reviewer / admin) |
| API key rotation | Keys rotatable without service interruption |
| Audit log integrity | Audit logs append-only, cryptographically signed |
| DPDP Act compliance | All personally-identifiable metadata handled per India's Digital Personal Data Protection Act 2023 |
| Vulnerability scanning | Dependency scanning in CI/CD pipeline |

---

## 26. Testing Strategy

### Unit Testing
- Each domain scorer tested independently against synthetic datasets covering all 0–4 score levels
- CQI engine tested against manual calculations across 50+ score combinations
- PRS engine tested against known re-identification risk scenarios
- Release classification engine tested against full matrix (all cell combinations)

### Integration Testing
- End-to-end assessment runs from file upload to report generation
- AIKosh webhook integration tested with mock AIKosh endpoint
- API contract tests (all endpoints against OpenAPI spec)

### Quality Framework Validation
- Run toolkit against real health research datasets from AIKosh, NDAP, and PhysioNet
- Compare automated scores to manual MIDAS-inspired expert assessment
- CQI accuracy target: ±5 points; PRS accuracy target: ±10 points

### Performance Testing
- Load test with 100 concurrent submissions (datasets of varying sizes: 10MB, 100MB, 1GB)
- Verify processing time < 3 minutes at p95

### Security Testing
- OWASP API security top 10 validation
- File upload security: malicious file rejection, path traversal prevention
- Penetration test on API endpoints

### Regression Testing
- Full assessment suite run on every deployment to catch scoring regressions
- Golden dataset suite (fixed datasets with known expected scores)

---

## 27. Acceptance Criteria

The toolkit is considered ready for deployment when:

1. All 15 MIDAS domains are implemented and producing scores for all supported file formats
2. CQI computation is verifiably correct (formula matches MIDAS 2.0 specification)
3. PRS computation produces results consistent with manual calculation on test cases
4. Release classification matches expected output for all 16 cells of the CQI×PRS matrix
5. Full quality report (JSON + HTML) generated for every assessment
6. AIKosh integration layer successfully POSTs quality metadata to mock AIKosh endpoint
7. Processing time < 3 minutes for a 1GB dataset at p95
8. Audit log is complete and reproducible for every assessment
9. All domain scorers produce a confidence level and rationale string
10. Dashboard renders domain radar chart, CQI gauge, PRS gauge, and release badge correctly
11. All API endpoints return correct status codes and response schemas per OpenAPI spec
12. Security: no critical or high-severity vulnerabilities in final security scan
13. Unit test coverage ≥ 80% across scoring engine modules

---

## 28. Risks & Limitations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| MIDAS 2.0 scoring criteria change post-Delphi review | Medium | High | Design framework as configuration-driven; domain criteria defined in YAML config files, not hardcoded |
| Automated scoring cannot fully replicate expert human judgment | High | Medium | Clearly communicate scores are automated estimates, not official MIDAS certification; provide confidence levels |
| Domain 1 (Annotation) scoring limited for datasets with no annotation columns | High | Low | Score based on metadata form responses; flag low confidence where file-based evidence unavailable |
| Domains relying on metadata form may produce inflated scores if custodian over-reports | Medium | High | Flag metadata-form-heavy domains with lower confidence; require evidence attachments for high scores on critical domains |
| AIKosh API integration specifications not fully public | Medium | High | Build integration layer with configurable webhook URL and payload schema; design for easy adaptation |
| Large datasets (>5GB) exceed processing time targets | Medium | Low | Implement sampling-based profiling for large files; clearly disclose sampling in reports |
| Privacy-sensitive data uploaded to toolkit | Medium | High | Keep files in secure private object storage under strict tenant isolation, and allow users to manually delete raw files and reports at any time |
| ICMR objects to toolkit claiming MIDAS alignment | Low | High | Clearly label as "MIDAS-inspired"; do not claim official MIDAS certification; document all inferences |

---

## 29. Assumptions Log

| # | Assumption | Confidence | If Wrong |
|---|---|---|---|
| A1 | Equal domain weighting (1/15 each) | Medium | Update when official weights published |
| A2 | CQI formula: (sum/60)×100 is as stated on MIDAS website | High | Confirmed from public source |
| A3 | PRS bands (0–15/16–40/41–70/71–100) are as stated | High | Confirmed from public Lite Version |
| A4 | Sensitivity multipliers (1.0×/1.5×/2.0×) are as documented in public Lite Version snippets | High | Adjust per full Annexure I if obtained |
| A5 | Domain 13 scores 3 (neutral) when no models are linked | Medium | Adjust if MIDAS clarifies this should be N/A |
| A6 | Kappa thresholds for Domain 1 are 0.6 and 0.8 | Medium | Adjust to match official sub-criteria if released |
| A7 | Column completeness ≥ 90% maps to Score 3 in Domain 5 | Medium | Adjust per official FHIR/health data completeness standards |
| A8 | MIDAS 2.0 is in its final public form post-Delphi review | Low | Framework may change; design scoring as config-driven |

---

## 30. Future Roadmap

### V2 — Intelligence Layer
- AI-assisted gap analysis and improvement recommendations per domain
- Natural language summary of quality report (LLM-generated)
- Automated suggestion of missing metadata fields
- Cross-dataset benchmarking (compare CQI distribution within health research sub-domains)

### V3 — Ecosystem Features
- Dataset version tracking (CQI/PRS delta between versions)
- Formal ICMR Nodal Centre workflow integration (toolkit pre-assessment feeds into official MIDAS review queue)
- Multi-language report support (Hindi, regional languages)
- Historical trend analytics across the AIKosh health dataset catalog
- Quality-weighted dataset discovery (search by CQI band, PRS band, release class)

### V4 — Advanced Assessment
- Imaging dataset assessment support (DICOM deep profiling)
- Federated assessment for datasets that cannot leave their host institution
- Real-time streaming dataset quality monitoring
- Integration with India's DPDP Act compliance verification systems

---

## 31. Deliverables

| Deliverable | Description |
|---|---|
| This PRD | Product Requirements Document (this document) |
| Quality Assessment Framework Specification | Standalone detailed spec of all 15 domain scoring rules (derived from Section 18) |
| Technical Design Document (TDD) | System architecture, database schema, API contracts, deployment design |
| OpenAPI Specification | Machine-readable API contract for all endpoints |
| `AGENTS.md` | AI agent orientation guide for any developer or agent picking up the codebase |
| Authentication System | JWT session cookie auth + bcrypt + Redis rate limiting + API key management |
| Admin Panel (Next.js) | User list, suspend/reactivate controls (role=admin only) |
| Assessment Engine (Python) | Rule-based scoring engine for all 15 domains |
| CQI & PRS Engines (Python) | Formula-based computation modules |
| Dataset Profiler (Python) | Statistical and structural dataset profiling module |
| Report Generator | JSON + HTML + PDF report generation module |
| AIKosh Integration Layer | REST API + webhook client for AIKosh integration |
| Dashboard (Next.js + TypeScript) | Frontend for quality results visualisation (Radar chart, CQI/PRS gauges, domain table) |
| Assessment History Page | Per-user list of all past assessments |
| Test Suite | Unit + integration + validation tests |
| Deployment Package | Docker Compose + Kubernetes manifests |
| User Guide | Documentation for dataset custodians using the toolkit |
| Admin Guide | Documentation for AIKosh administrators configuring the toolkit |

---

## Appendix A — MIDAS Domain Metric Catalog

| Domain | Primary Automated Signal | Primary Metadata Signal | Confidence When Both Present |
|---|---|---|---|
| 1. Annotation Reliability | Label column detection, IRR in metadata | Annotator qualifications, protocol | Medium |
| 2. Metadata Completeness | DOI format validation, field completeness | Schema standard, registry link | High |
| 3. Documentation | Data dictionary file presence, description length | README quality | Medium |
| 4. Representativeness | Age/sex distribution from data | Site count, geography, sampling strategy | Medium |
| 5. Interoperability | Code pattern detection, completeness %, range checks | Declared standard | High |
| 6. AI Readiness | Class distribution, split columns, correlation matrix | Split documentation, benchmark info | High |
| 7. Privacy | Identifier heuristics, quasi-identifier granularity | De-identification method, epsilon | High |
| 8. Security | — | DUA, encryption, audit controls | Low (metadata only) |
| 9. Provenance | Pipeline file presence | Pipeline description | Medium |
| 10. Ethics | Demographic parity check | Ethics approval, consent type | Medium |
| 11. Synthetic Data | Synthetic % field | Utility and privacy test results | Low (metadata only) |
| 12. Stewardship | — | Governance policy, steward name | Low (metadata only) |
| 13. Model Linkage | — | Model IDs | Low (metadata only) |
| 14. Sustainability | Compression ratio | Sustainability documentation | Low |
| 15. Curation | Version format, changelog presence | Feedback mechanism | Medium |

---

## Appendix B — Sample Quality Report Output

```json
{
  "assessment_id": "a3f7c2d1-9b4e-4f2a-bc31-7d8e9f1a2b3c",
  "dataset_id": "aikosh-hrd-00421",
  "dataset_name": "Multi-site TB Cohort Study — India 2019–2023",
  "assessed_at": "2026-06-17T10:34:22Z",
  "toolkit_version": "1.0.0",
  "domain_11_applicable": false,
  "cqi": 67.9,
  "cqi_band": "Silver",
  "prs": 22,
  "prs_band": "Moderate",
  "release_classification": "Controlled",
  "classification_note": "TB dataset defaults to Controlled per high-stigma policy regardless of PRS band",
  "domain_scores": {
    "1_annotation_labelling_reliability": { "score": 3, "max": 4, "confidence": "Medium" },
    "2_metadata_completeness": { "score": 3, "max": 4, "confidence": "High" },
    "3_documentation_user_guidance": { "score": 2, "max": 4, "confidence": "High" },
    "4_population_representativeness": { "score": 3, "max": 4, "confidence": "Medium" },
    "5_data_structure_interoperability": { "score": 3, "max": 4, "confidence": "High" },
    "6_ai_analytics_readiness": { "score": 2, "max": 4, "confidence": "High" },
    "7_privacy_identifiability": { "score": 4, "max": 4, "confidence": "High" },
    "8_security_access_governance": { "score": 3, "max": 4, "confidence": "Low" },
    "9_provenance_workflow_transparency": { "score": 2, "max": 4, "confidence": "Medium" },
    "10_ethical_social_accountability": { "score": 3, "max": 4, "confidence": "Medium" },
    "11_synthetic_simulated_data": { "score": null, "max": null, "confidence": null, "note": "N/A" },
    "12_stewardship_governance": { "score": 3, "max": 4, "confidence": "Low" },
    "13_model_linkage_integrity": { "score": 3, "max": 4, "confidence": "Low", "note": "No linked models; neutral score applied" },
    "14_environmental_sustainability": { "score": 1, "max": 4, "confidence": "Low" },
    "15_continuous_curation_feedback": { "score": 2, "max": 4, "confidence": "Medium" }
  },
  "cqi_computation": {
    "sum_of_scores": 38,
    "max_possible": 56,
    "formula": "(38 / 56) × 100",
    "cqi": 67.9
  },
  "gaps": [
    "Domain 3: No data dictionary uploaded. Score capped at 2.",
    "Domain 6: No train/test split defined. No class balance analysis present.",
    "Domain 9: Processing pipeline described narratively but no executable scripts uploaded.",
    "Domain 14: No sustainability information provided.",
    "Domain 15: No changelog. Version history not documented."
  ],
  "strengths": [
    "Domain 7: Full de-identification with documented methodology. No direct identifiers detected.",
    "Domain 5: ICD-10 codes detected in diagnosis columns. Column completeness 94.2%.",
    "Domain 4: 14 sites across 7 states. Age and sex distribution documented."
  ]
}
```

---

## Appendix C — PRS Calculation Worked Example

**Dataset:** Multi-site TB Cohort Study

**Step 1 — Identifier Risk Assessment:**
- Direct identifiers detected by profiler: None
- Location granularity: District level
- Temporal granularity: Month of diagnosis
- Rare condition + village + date combination: No (district-level, not village)
- Baseline risk from identification: **15** (only coarse info: age, sex, district, month)

**Step 2 — Sensitivity Class:**
- TB data → High Stigma / Personal Impact → multiplier = **1.5×**

**Step 3 — PRS Computation:**
```
AdjustedRisk = 15 × 1.5 = 22.5
PRS = round(22.5) = 23 ≈ 22 (rounded)
PRS Band = Moderate (16–40)
```

**Step 4 — Release Classification:**
- TB is high-stigma → defaults to Controlled regardless of PRS band
- Release classification: **Controlled**

---

## Appendix D — Dataset Sources for Validation

The following publicly available datasets are recommended for validating the toolkit's scoring engine during development and testing:

| Source | Dataset | Format | Why Useful |
|---|---|---|---|
| AIKosh (aikosh.indiaai.gov.in) | Health sector datasets | Various | Directly in-ecosystem; most representative of real submissions |
| NDAP (ndap.gov.in) | NFHS-5 health indicators, disease surveillance | CSV | Indian epidemiological data; tests Domain 4 (representativeness) |
| PhysioNet (physionet.org) | MIMIC-IV (demo), MIMIC-III | CSV | Well-annotated, high-quality reference — expected high CQI |
| CTRI (ctri.nic.in) | Clinical trial metadata | Various | Tests Domain 10 (ethics), Domain 2 (metadata) |
| data.gov.in | ICMR published datasets | CSV/XLSX | Government health research datasets; realistic quality range |

**Note:** No training data is required. Datasets are used only to validate that the automated scoring engine produces defensible scores across a range of quality levels.

---

*End of Document*

---

**Document History**

| Version | Date | Author | Notes |
|---|---|---|---|
| 0.1 | June 17, 2026 | — | Initial draft based on MIDAS public knowledge extraction and AIKosh platform research |
| 1.0 | June 17, 2026 | — | First complete version |
| 1.1 | June 24, 2026 | — | Realigned to full-stack app architecture. Updated §1 (executive summary), §19 (API endpoints table — added auth, admin, upload-url endpoints), §20 (tech stack: Next.js + TS + Tailwind + shadcn/ui), §22 (DB overview: added users and api_keys tables as root entities), §31 (deliverables: added AGENTS.md, auth system, admin panel, assessment history). |
