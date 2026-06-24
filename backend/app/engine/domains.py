"""
=============================================================================
15 MIDAS Domain Scorers — backend/app/engine/domains.py
=============================================================================
Each class here scores ONE domain (0 to 4) using:
  - self.profile  → stats produced by the Profiler (from the actual data file)
  - self.metadata → answers from the user's questionnaire form
  - self.criteria → thresholds and rules loaded from domain_criteria.yaml

Every scorer:
  1. Collects evidence (things that are GOOD → raise the score)
  2. Collects gaps    (things that are MISSING → lower the score)
  3. Returns a DomainScoreResult with score 0-4, rationale, evidence, gaps
=============================================================================
"""

from app.engine.scoring import BaseDomainScorer, DomainScoreResult


# =============================================================================
# DOMAIN 1 — Annotation / Labelling Reliability
# Question: How good are the human-made labels on the dataset?
# =============================================================================
class AnnotationScorer(BaseDomainScorer):
    DOMAIN_NUMBER = 1
    DOMAIN_NAME   = "Annotation / Labelling Reliability"

    def score(self) -> DomainScoreResult:
        evidence = []
        gaps     = []

        # Load the thresholds from YAML config
        # irr_adequate = the minimum acceptable inter-rater reliability score (default 0.6)
        # irr_exemplary = what counts as excellent IRR (default 0.8)
        irr_adequate  = self.criteria.get("thresholds", {}).get("irr_adequate", 0.6)
        irr_exemplary = self.criteria.get("thresholds", {}).get("irr_exemplary", 0.8)
        min_annotators = self.criteria.get("thresholds", {}).get("min_annotators", 2)

        # Read the user's questionnaire answers
        annotation_methodology = self.metadata.get("annotation_methodology")  # Description of how labelling was done
        num_annotators         = self.metadata.get("num_annotators")           # How many people labelled
        irr_method             = self.metadata.get("irr_method")               # e.g. "Cohen's Kappa"
        irr_value              = self.metadata.get("irr_value")                # e.g. 0.75

        # --- SCORE 0: No annotation information provided at all
        if not annotation_methodology and not irr_method:
            gaps.append("No annotation methodology or IRR metric provided.")
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=0, rationale="No annotation information provided.",
                evidence_items=evidence, gaps=gaps, confidence="High"
            )

        # At least SOME annotation info was provided
        if annotation_methodology:
            evidence.append(f"Annotation methodology described: '{annotation_methodology[:80]}'")

        # --- Check IRR (inter-rater reliability) value
        if irr_value is None:
            gaps.append("No inter-rater reliability (IRR) metric provided.")
            # Score 1 if annotations exist but no IRR metric
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=1, rationale="Annotations exist but no IRR metric reported.",
                evidence_items=evidence, gaps=gaps, confidence="Medium"
            )

        evidence.append(f"IRR method: {irr_method or 'unspecified'}, value: {irr_value}")

        if irr_value < irr_adequate:
            # IRR is below minimum threshold
            gaps.append(f"IRR {irr_value} is below the adequate threshold of {irr_adequate}.")
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=2, rationale=f"Annotators qualified but IRR {irr_value} < {irr_adequate}.",
                evidence_items=evidence, gaps=gaps, confidence="High"
            )

        # IRR >= adequate threshold → at least Score 3
        evidence.append(f"IRR {irr_value} meets the adequate threshold ({irr_adequate}).")

        if irr_value >= irr_exemplary and num_annotators and num_annotators >= min_annotators:
            # All conditions for Score 4 met
            evidence.append(f"Exemplary IRR ({irr_value} >= {irr_exemplary}) with {num_annotators} annotators.")
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=4, rationale=f"Excellent IRR {irr_value} with {num_annotators} independent annotators.",
                evidence_items=evidence, gaps=gaps, confidence="High"
            )
        else:
            if irr_value < irr_exemplary:
                gaps.append(f"IRR {irr_value} < exemplary threshold {irr_exemplary}.")
            if not num_annotators or num_annotators < min_annotators:
                gaps.append(f"Fewer than {min_annotators} annotators recorded.")

            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=3, rationale=f"Good IRR {irr_value} with documented methodology.",
                evidence_items=evidence, gaps=gaps, confidence="High"
            )


# =============================================================================
# DOMAIN 2 — Metadata Completeness
# Question: Is the dataset described well with rich, machine-readable metadata?
# =============================================================================
class MetadataCompletenessScorer(BaseDomainScorer):
    DOMAIN_NUMBER = 2
    DOMAIN_NAME   = "Metadata Completeness"

    def score(self) -> DomainScoreResult:
        evidence = []
        gaps     = []

        dataset_name          = self.metadata.get("dataset_name")            # Must exist
        dataset_version       = self.metadata.get("dataset_version")         # Version number
        persistent_identifier = self.metadata.get("persistent_identifier")   # DOI or accession number
        standards_used        = self.metadata.get("standards_used")          # e.g. "DataCite, DCAT"
        changelog_provided    = self.metadata.get("changelog_provided", False)
        version_format        = self.metadata.get("version_format", "none")

        # --- SCORE 0: No metadata at all (but dataset_name is required, so this is edge case)
        if not dataset_name:
            gaps.append("Dataset name not provided — no usable metadata.")
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=0, rationale="No metadata provided beyond the file.",
                evidence_items=evidence, gaps=gaps, confidence="High"
            )

        evidence.append(f"Dataset name provided: '{dataset_name}'")

        # Does it have a version and standards?
        has_version   = bool(dataset_version)
        has_standards = bool(standards_used)
        has_doi       = bool(persistent_identifier)
        has_changelog = bool(changelog_provided)
        has_semver    = version_format == "semantic"

        if has_version:
            evidence.append(f"Dataset version: {dataset_version}")
        else:
            gaps.append("No dataset version provided.")

        if not has_standards:
            gaps.append("No metadata standard referenced (e.g. DataCite, DCAT, schema.org).")

        if not has_doi:
            gaps.append("No persistent identifier (DOI or accession number) provided.")
        else:
            evidence.append(f"Persistent identifier: {persistent_identifier}")

        if has_changelog:
            evidence.append("Changelog provided — versioning is tracked.")

        if has_semver:
            evidence.append("Semantic versioning format used.")

        # Determine score based on what's present
        if not has_version and not has_standards:
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=1, rationale="Basic metadata only — no standards, no version.",
                evidence_items=evidence, gaps=gaps, confidence="High"
            )
        if not has_doi:
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=2, rationale="Structured metadata present but no persistent identifier.",
                evidence_items=evidence, gaps=gaps, confidence="High"
            )
        if has_doi and has_standards:
            if has_changelog and has_semver:
                return DomainScoreResult(
                    domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                    score=4, rationale="Machine-actionable, versioned metadata with DOI and standard.",
                    evidence_items=evidence, gaps=gaps, confidence="High"
                )
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=3, rationale="Metadata follows recognised schema with persistent identifier.",
                evidence_items=evidence, gaps=gaps, confidence="High"
            )

        return DomainScoreResult(
            domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
            score=2, rationale="Some structured metadata present but key fields missing.",
            evidence_items=evidence, gaps=gaps, confidence="Medium"
        )


# =============================================================================
# DOMAIN 3 — Documentation & User Guidance
# Question: How well explained is this dataset for someone who wants to use it?
# =============================================================================
class DocumentationScorer(BaseDomainScorer):
    DOMAIN_NUMBER = 3
    DOMAIN_NAME   = "Documentation & User Guidance"

    def score(self) -> DomainScoreResult:
        evidence = []
        gaps     = []

        data_dict_uploaded    = self.metadata.get("data_dictionary_uploaded", False)
        github_repo_url       = self.metadata.get("github_repo_url")
        changelog_provided    = self.metadata.get("changelog_provided", False)
        target_population     = self.metadata.get("target_population", "")

        # A description of at least 20 chars is the minimum
        has_description = len(target_population or "") >= 20

        if not has_description:
            gaps.append("Target population description too brief or not provided.")
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=0, rationale="No meaningful documentation provided.",
                evidence_items=evidence, gaps=gaps, confidence="High"
            )

        evidence.append("Target population description provided.")

        if not data_dict_uploaded:
            gaps.append("No data dictionary uploaded.")
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=1, rationale="Minimal description only — no data dictionary.",
                evidence_items=evidence, gaps=gaps, confidence="High"
            )

        evidence.append("Data dictionary uploaded.")

        if not changelog_provided and not github_repo_url:
            gaps.append("No changelog and no GitHub/code repository URL provided.")
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=2, rationale="README/data dictionary present, but no changelog or code repo.",
                evidence_items=evidence, gaps=gaps, confidence="High"
            )

        if changelog_provided:
            evidence.append("Changelog provided.")
        if github_repo_url:
            evidence.append(f"Code repository: {github_repo_url}")

        if data_dict_uploaded and changelog_provided and github_repo_url:
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=4, rationale="Full documentation with data dict, changelog, and code repo.",
                evidence_items=evidence, gaps=gaps, confidence="High"
            )

        return DomainScoreResult(
            domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
            score=3, rationale="Full data dictionary and collection methodology described.",
            evidence_items=evidence, gaps=gaps, confidence="High"
        )


# =============================================================================
# DOMAIN 4 — Population Representativeness
# Question: Does the data cover a wide, diverse population?
# =============================================================================
class RepresentativenessScorer(BaseDomainScorer):
    DOMAIN_NUMBER = 4
    DOMAIN_NAME   = "Population Representativeness"

    def score(self) -> DomainScoreResult:
        evidence = []
        gaps     = []

        target_population   = self.metadata.get("target_population", "")
        geographic_coverage = self.metadata.get("geographic_coverage")
        num_sites           = self.metadata.get("num_sites")
        sex_distribution    = self.metadata.get("sex_distribution", "not_specified")
        age_range_min       = self.metadata.get("age_range_min")
        age_range_max       = self.metadata.get("age_range_max")

        min_sites = self.criteria.get("thresholds", {}).get("multi_site_min", 2)

        if not target_population or len(target_population) < 20:
            gaps.append("No target population description provided.")
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=0, rationale="No population description provided.",
                evidence_items=evidence, gaps=gaps, confidence="High"
            )

        evidence.append(f"Target population described: '{target_population[:60]}'")

        is_multi_site = num_sites and num_sites >= min_sites
        is_multi_region = geographic_coverage in ("state", "national", "multi_country")
        has_sex_both = sex_distribution == "both"
        has_age_range = age_range_min is not None and age_range_max is not None
        wide_age_range = has_age_range and (age_range_max - age_range_min) >= 40

        if not is_multi_site:
            gaps.append(f"Single site or fewer than {min_sites} sites reported.")

        if not is_multi_region:
            gaps.append(f"Geographic coverage is limited to '{geographic_coverage}'.")

        if not has_sex_both:
            gaps.append(f"Sex distribution is '{sex_distribution}' — not both sexes.")

        # Profile-based data checks (from profiler output)
        age_dist = self.profile.get("age_distribution", {})
        if age_dist:
            evidence.append(
                f"Age distribution from data: <18={age_dist.get('under_18_pct',0)}%, "
                f"18-60={age_dist.get('18_to_60_pct',0)}%, >60={age_dist.get('over_60_pct',0)}%"
            )

        score = 0
        if target_population:
            score = 1
        if is_multi_site or is_multi_region:
            score = 2
        if is_multi_site and is_multi_region and has_sex_both:
            score = 3
        if score == 3 and wide_age_range:
            score = 4

        return DomainScoreResult(
            domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
            score=score, rationale=f"Score {score}: Based on site count, geographic coverage, and demographics.",
            evidence_items=evidence, gaps=gaps, confidence="High"
        )


# =============================================================================
# DOMAIN 5 — Data Structure & Interoperability
# Question: Does the dataset use healthcare standards and have complete data?
# =============================================================================
class InteroperabilityScorer(BaseDomainScorer):
    DOMAIN_NUMBER = 5
    DOMAIN_NAME   = "Data Structure & Interoperability"

    def score(self) -> DomainScoreResult:
        evidence = []
        gaps     = []

        completeness_threshold = self.criteria.get("thresholds", {}).get("completeness_pct", 90.0)
        standards_used = self.metadata.get("standards_used")

        # Get data-driven facts from the profiler
        completeness   = self.profile.get("completeness", {})
        overall_pct    = completeness.get("overall_pct", 0.0)
        standards      = self.profile.get("standards_detected", {})
        icd_detected   = standards.get("icd_codes_present", False)
        snomed_detected= standards.get("snomed_codes_present", False)
        loinc_detected = standards.get("loinc_codes_present", False)
        schema         = self.profile.get("schema_consistency", {})
        violations     = schema.get("schema_violations", 0)

        data_standard_detected = icd_detected or snomed_detected or loinc_detected

        if data_standard_detected:
            detected_names = []
            if icd_detected:   detected_names.append("ICD-10")
            if snomed_detected: detected_names.append("SNOMED-CT")
            if loinc_detected:  detected_names.append("LOINC")
            evidence.append(f"Medical coding standards detected in data: {', '.join(detected_names)}")
        else:
            gaps.append("No recognised medical coding standard (ICD, SNOMED, LOINC) detected in data columns.")

        if not standards_used:
            gaps.append("No standard declared in metadata form.")
        else:
            evidence.append(f"Standard declared in metadata: {standards_used}")

        evidence.append(f"Overall data completeness: {overall_pct}%")
        if overall_pct < completeness_threshold:
            gaps.append(f"Overall completeness {overall_pct}% is below the required {completeness_threshold}%.")

        cols_below_90 = completeness.get("columns_below_90pct", [])
        if cols_below_90:
            gaps.append(f"Columns below 90% completeness: {cols_below_90[:5]}")

        if violations > 0:
            gaps.append(f"{violations} schema violations detected (impossible values like negative age).")
        else:
            evidence.append("No schema violations found.")

        # Score logic
        if not data_standard_detected:
            if not standards_used:
                score = 0
            else:
                score = 1   # Declared standard but not actually found in data
        else:
            if overall_pct < completeness_threshold:
                score = 2   # Standard found but completeness insufficient
            else:
                score = 3 if violations > 0 else 4

        return DomainScoreResult(
            domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
            score=score, rationale=f"Score {score}: completeness={overall_pct}%, standards={data_standard_detected}.",
            evidence_items=evidence, gaps=gaps, confidence="High"
        )


# =============================================================================
# DOMAIN 6 — AI / Analytics Readiness
# Question: Is this dataset well-packaged for training machine learning models?
# =============================================================================
class AIReadinessScorer(BaseDomainScorer):
    DOMAIN_NUMBER = 6
    DOMAIN_NAME   = "AI / Analytics Readiness"

    def score(self) -> DomainScoreResult:
        evidence = []
        gaps     = []

        imbalance_ok_threshold = self.criteria.get("thresholds", {}).get("imbalance_ratio_ok", 3.0)

        # From profiler
        label_info    = self.profile.get("label_columns", {})
        split_info    = self.profile.get("split_columns", {})
        has_label     = label_info.get("binary_label_detected", False) or label_info.get("label_column") is not None
        label_col     = label_info.get("label_column")
        imbalance     = label_info.get("imbalance_ratio")
        split_present = split_info.get("split_column_detected", False)
        fold_present  = split_info.get("fold_column_detected", False)

        if not has_label:
            gaps.append("No label/target column detected in dataset.")
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=0, rationale="No ML target column detected — raw data dump.",
                evidence_items=evidence, gaps=gaps, confidence="High"
            )

        evidence.append(f"Target/label column detected: '{label_col}'")

        if imbalance:
            evidence.append(f"Class imbalance ratio: {imbalance}x")
            if imbalance > imbalance_ok_threshold:
                gaps.append(f"Imbalance ratio {imbalance} > acceptable threshold {imbalance_ok_threshold}.")

        if not split_present and not fold_present:
            gaps.append("No train/test split or fold column detected.")
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=1, rationale="Label column present but no train/test split defined.",
                evidence_items=evidence, gaps=gaps, confidence="High"
            )

        if split_present:
            evidence.append("Train/test split column detected.")
        if fold_present:
            evidence.append("Cross-validation fold column detected.")

        if imbalance and imbalance > imbalance_ok_threshold:
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=2, rationale="Split defined but class imbalance not addressed.",
                evidence_items=evidence, gaps=gaps, confidence="High"
            )

        return DomainScoreResult(
            domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
            score=3, rationale="Pre-defined splits with acceptable class balance.",
            evidence_items=evidence, gaps=gaps, confidence="High"
        )


# =============================================================================
# DOMAIN 7 — Privacy & Identifiability
# Question: Could someone identify real patients from this data?
# =============================================================================
class PrivacyScorer(BaseDomainScorer):
    DOMAIN_NUMBER = 7
    DOMAIN_NAME   = "Privacy & Identifiability"

    def score(self) -> DomainScoreResult:
        evidence = []
        gaps     = []

        # Check if the profiler found direct identifiers (names, phone, GPS, DOB)
        pii = self.profile.get("pii_scan", {})
        direct_ids = pii.get("direct_identifiers_detected", False)

        if direct_ids:
            # If real names/phones/GPS are found in the file → automatic Score 0
            found = []
            if pii.get("name_columns"):  found.append(f"names: {pii['name_columns']}")
            if pii.get("phone_columns"): found.append(f"phones: {pii['phone_columns']}")
            if pii.get("gps_columns"):   found.append(f"GPS: {pii['gps_columns']}")
            if pii.get("dob_columns"):   found.append(f"DOB: {pii['dob_columns']}")
            gaps.append(f"Direct identifiers detected in columns — {'; '.join(found)}")
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=0, rationale="Direct identifiers (names, phone, GPS) found in dataset columns.",
                evidence_items=evidence, gaps=gaps, confidence="High"
            )

        evidence.append("No direct identifiers detected in column scan.")

        # Now check questionnaire answers about de-identification
        deident_method = self.metadata.get("deidentification_method")
        dp_applied     = self.metadata.get("differential_privacy_applied", False)
        dp_epsilon     = self.metadata.get("dp_epsilon")

        if not deident_method:
            gaps.append("No de-identification method documented in metadata form.")
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=1, rationale="No direct identifiers detected but no de-identification method documented.",
                evidence_items=evidence, gaps=gaps, confidence="Medium"
            )

        evidence.append(f"De-identification method documented: '{deident_method}'")

        if dp_applied and dp_epsilon:
            evidence.append(f"Differential Privacy applied with ε={dp_epsilon}.")
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=4, rationale=f"Differential Privacy applied (ε={dp_epsilon}) — strongest protection.",
                evidence_items=evidence, gaps=gaps, confidence="High"
            )

        if "k-anonymity" in (deident_method or "").lower():
            evidence.append("k-anonymity method declared.")
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=4, rationale="k-anonymity declared — formally verified anonymisation.",
                evidence_items=evidence, gaps=gaps, confidence="High"
            )

        return DomainScoreResult(
            domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
            score=3, rationale="Formal de-identification applied and documented.",
            evidence_items=evidence, gaps=gaps, confidence="High"
        )


# =============================================================================
# DOMAIN 8 — Security & Access Governance
# Question: Are there proper access controls protecting this dataset?
# =============================================================================
class SecurityScorer(BaseDomainScorer):
    DOMAIN_NUMBER = 8
    DOMAIN_NAME   = "Security & Access Governance"

    def score(self) -> DomainScoreResult:
        evidence = []
        gaps     = []

        access_control = self.metadata.get("access_control_method")
        consent_type   = self.metadata.get("consent_type", "not_applicable")

        if not access_control:
            gaps.append("No access control method documented.")
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=0, rationale="No access control — dataset has no documented protections.",
                evidence_items=evidence, gaps=gaps, confidence="High"
            )

        evidence.append(f"Access control method: '{access_control}'")
        access_lower = access_control.lower()

        has_dua         = "dua" in access_lower or "data use agreement" in access_lower
        has_encryption  = "encrypt" in access_lower
        has_audit_trail = "audit" in access_lower or "log" in access_lower
        has_login       = "login" in access_lower or "auth" in access_lower

        if has_dua:
            evidence.append("Data Use Agreement (DUA) mentioned.")
        if has_encryption:
            evidence.append("Encryption mentioned in access control description.")
        if has_audit_trail:
            evidence.append("Audit trail/log mentioned.")

        if not has_login and not has_dua:
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=1, rationale="Basic access control exists but no formal policy.",
                evidence_items=evidence, gaps=gaps, confidence="Medium"
            )

        if has_login and not has_dua:
            gaps.append("No DUA or user verification process documented.")
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=2, rationale="Formal access policy exists but no DUA.",
                evidence_items=evidence, gaps=gaps, confidence="High"
            )

        if has_dua and not has_encryption:
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=3, rationale="DUA and access process documented.",
                evidence_items=evidence, gaps=gaps, confidence="High"
            )

        return DomainScoreResult(
            domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
            score=4, rationale="DUA + encryption + audit trail — comprehensive security.",
            evidence_items=evidence, gaps=gaps, confidence="High"
        )


# =============================================================================
# DOMAIN 9 — Provenance & Workflow Transparency
# Question: Can you trace exactly how this data went from raw collection to release?
# =============================================================================
class ProvenanceScorer(BaseDomainScorer):
    DOMAIN_NUMBER = 9
    DOMAIN_NAME   = "Provenance & Workflow Transparency"

    def score(self) -> DomainScoreResult:
        evidence = []
        gaps     = []

        provenance_available = self.metadata.get("provenance_pipeline_available", False)
        github_url           = self.metadata.get("github_repo_url")
        annotation_method    = self.metadata.get("annotation_methodology")

        if not annotation_method and not provenance_available:
            gaps.append("No provenance or pipeline information provided.")
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=0, rationale="No provenance information provided at all.",
                evidence_items=evidence, gaps=gaps, confidence="High"
            )

        if annotation_method:
            evidence.append("Data collection methodology described in metadata.")

        if not provenance_available:
            gaps.append("No executable pipeline or processing script uploaded.")
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=2, rationale="Processing steps described in narrative but not as executable pipeline.",
                evidence_items=evidence, gaps=gaps, confidence="High"
            )

        evidence.append("Provenance pipeline declared as available.")

        if github_url:
            evidence.append(f"Pipeline hosted on GitHub: {github_url}")
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=4, rationale="Fully executable, version-controlled pipeline on GitHub.",
                evidence_items=evidence, gaps=gaps, confidence="High"
            )

        return DomainScoreResult(
            domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
            score=3, rationale="Documented pipeline with version-controlled scripts.",
            evidence_items=evidence, gaps=gaps, confidence="High"
        )


# =============================================================================
# DOMAIN 10 — Ethical & Social Accountability
# Question: Was the data collected ethically with proper consent?
# =============================================================================
class EthicsScorer(BaseDomainScorer):
    DOMAIN_NUMBER = 10
    DOMAIN_NAME   = "Ethical & Social Accountability"

    def score(self) -> DomainScoreResult:
        evidence = []
        gaps     = []

        ethics_ref      = self.metadata.get("ethics_approval_ref")
        consent_type    = self.metadata.get("consent_type", "not_applicable")
        num_sites       = self.metadata.get("num_sites", 1)
        sex_distribution = self.metadata.get("sex_distribution", "not_specified")

        if not ethics_ref:
            gaps.append("No ethics approval reference number provided.")
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=0, rationale="No ethics approval and no consent documentation.",
                evidence_items=evidence, gaps=gaps, confidence="High"
            )

        evidence.append(f"Ethics approval reference: '{ethics_ref}'")

        if consent_type == "not_applicable":
            gaps.append("Consent type not specified.")
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=1, rationale="Ethics approval obtained but consent not documented.",
                evidence_items=evidence, gaps=gaps, confidence="High"
            )

        evidence.append(f"Consent type: {consent_type}")

        # Data-driven equity check: was there diversity in sex/sites?
        both_sexes   = sex_distribution == "both"
        multi_site   = num_sites and num_sites >= 2
        equity_check = both_sexes and multi_site

        if not equity_check:
            if not both_sexes:
                gaps.append(f"Sex distribution is '{sex_distribution}' — missing equity coverage.")
            if not multi_site:
                gaps.append("Single-site data — limited geographic equity.")
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=2, rationale="Ethics + consent documented but no equity analysis.",
                evidence_items=evidence, gaps=gaps, confidence="High"
            )

        evidence.append(f"Equity signals: both sexes = {both_sexes}, multi-site = {multi_site}.")
        return DomainScoreResult(
            domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
            score=3, rationale="Ethics approval, consent documented, equity analysis signals present.",
            evidence_items=evidence, gaps=gaps, confidence="High"
        )


# =============================================================================
# DOMAIN 11 — Synthetic / Simulated Data  (may be N/A)
# Question: If synthetic data exists, is it properly evaluated?
# =============================================================================
class SyntheticDataScorer(BaseDomainScorer):
    DOMAIN_NUMBER = 11
    DOMAIN_NAME   = "Synthetic / Simulated Data"

    def score(self) -> DomainScoreResult:
        evidence = []
        gaps     = []

        synthetic_pct = self.metadata.get("synthetic_data_pct")

        # If the user said 0% or didn't answer → domain is NOT APPLICABLE
        if synthetic_pct is None or synthetic_pct == 0:
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=None, not_applicable=True,
                rationale="Dataset contains no synthetic data — domain not applicable.",
                evidence_items=[], gaps=[], confidence="High"
            )

        evidence.append(f"Synthetic data percentage: {synthetic_pct}%")

        # The user declared synthetic data exists → start scoring
        dp_applied = self.metadata.get("differential_privacy_applied", False)
        dp_epsilon = self.metadata.get("dp_epsilon")

        if not dp_applied:
            gaps.append("No privacy analysis (differential privacy) on synthetic data.")
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=0, rationale="Synthetic data present but no utility or privacy evaluation.",
                evidence_items=evidence, gaps=gaps, confidence="Medium"
            )

        evidence.append("Differential privacy applied to synthetic data.")
        if dp_epsilon:
            evidence.append(f"DP epsilon = {dp_epsilon}")
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=4, rationale="Synthetic data with documented DP privacy analysis and epsilon.",
                evidence_items=evidence, gaps=gaps, confidence="High"
            )

        return DomainScoreResult(
            domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
            score=3, rationale="Synthetic data with privacy analysis — epsilon not documented.",
            evidence_items=evidence, gaps=gaps, confidence="Medium"
        )


# =============================================================================
# DOMAIN 12 — Stewardship & Governance
# Question: Does the organisation have formal data stewardship policies?
# =============================================================================
class StewardshipScorer(BaseDomainScorer):
    DOMAIN_NUMBER = 12
    DOMAIN_NAME   = "Stewardship & Governance"

    def score(self) -> DomainScoreResult:
        evidence = []
        gaps     = []

        access_control = self.metadata.get("access_control_method", "")
        license_type   = self.metadata.get("license_type")
        changelog      = self.metadata.get("changelog_provided", False)
        consent_type   = self.metadata.get("consent_type", "not_applicable")

        if not access_control and not license_type:
            gaps.append("No governance structure — no access policy, no license.")
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=0, rationale="No governance structure or named data steward.",
                evidence_items=evidence, gaps=gaps, confidence="High"
            )

        if license_type:
            evidence.append(f"License type declared: {license_type}")
        if access_control:
            evidence.append(f"Access control method: {access_control}")

        has_policy    = bool(access_control)
        has_license   = bool(license_type)
        has_changelog = bool(changelog)
        has_consent   = consent_type != "not_applicable"

        if not has_policy:
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=1, rationale="Named governance elements exist but no formal policy.",
                evidence_items=evidence, gaps=gaps, confidence="Medium"
            )

        if has_policy and not has_consent:
            gaps.append("Governance policy exists but consent/compliance basis not documented.")
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=2, rationale="Policy exists but not formally documented against regulations.",
                evidence_items=evidence, gaps=gaps, confidence="High"
            )

        if has_policy and has_consent and has_license:
            evidence.append("Consent type, license, and access policy all documented.")
            if has_changelog:
                evidence.append("Changelog present — lifecycle management tracked.")
                return DomainScoreResult(
                    domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                    score=4, rationale="Full governance policy with lifecycle management and changelog.",
                    evidence_items=evidence, gaps=gaps, confidence="High"
                )
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=3, rationale="Formal governance policy with compliance documentation.",
                evidence_items=evidence, gaps=gaps, confidence="High"
            )

        return DomainScoreResult(
            domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
            score=2, rationale="Partial governance — some elements missing.",
            evidence_items=evidence, gaps=gaps, confidence="Medium"
        )


# =============================================================================
# DOMAIN 13 — Model Linkage Integrity
# Question: If any ML models were trained on this data, are they properly documented?
# =============================================================================
class ModelLinkageScorer(BaseDomainScorer):
    DOMAIN_NUMBER = 13
    DOMAIN_NAME   = "Model Linkage Integrity"

    def score(self) -> DomainScoreResult:
        evidence = []
        gaps     = []

        linked_model_ids = self.metadata.get("linked_model_ids") or []

        # If no models linked → neutral score (3), not penalised
        if not linked_model_ids:
            evidence.append("No linked models — dataset not associated with any ML model. Neutral score applied.")
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=3,
                rationale="No linked models. Per MIDAS rules, absence of model linkage is not penalised.",
                evidence_items=evidence, gaps=gaps, confidence="Low"
            )

        evidence.append(f"{len(linked_model_ids)} linked model ID(s) provided: {linked_model_ids}")

        github_url       = self.metadata.get("github_repo_url")
        changelog        = self.metadata.get("changelog_provided", False)
        dataset_version  = self.metadata.get("dataset_version")

        has_ids          = bool(linked_model_ids)
        has_version_pin  = bool(dataset_version)
        has_code         = bool(github_url)
        has_changelog    = bool(changelog)

        if has_ids and not has_version_pin:
            gaps.append("Linked models found but dataset version not pinned.")
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=2, rationale="Model IDs provided but no dataset version pinning.",
                evidence_items=evidence, gaps=gaps, confidence="High"
            )

        if has_version_pin:
            evidence.append(f"Dataset version {dataset_version} pinned to model.")

        if has_code:
            evidence.append(f"Training code available at: {github_url}")
        if has_changelog:
            evidence.append("Changelog present — model-dataset version history tracked.")

        if has_ids and has_version_pin and has_code:
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=4, rationale="Model IDs, version pinning, and training code all documented.",
                evidence_items=evidence, gaps=gaps, confidence="High"
            )

        return DomainScoreResult(
            domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
            score=3, rationale="Model version pinned to dataset version.",
            evidence_items=evidence, gaps=gaps, confidence="High"
        )


# =============================================================================
# DOMAIN 14 — Environmental Sustainability
# Question: Is there any information about energy/carbon footprint?
# =============================================================================
class SustainabilityScorer(BaseDomainScorer):
    DOMAIN_NUMBER = 14
    DOMAIN_NAME   = "Environmental Sustainability"

    def score(self) -> DomainScoreResult:
        evidence = []
        gaps     = []

        sustainability_info = self.metadata.get("sustainability_info_provided", False)

        # DATA proxy: compression ratio from file size
        file_info     = self.profile.get("file", {})
        size_bytes    = file_info.get("size_bytes", 0)
        shape         = self.profile.get("shape", {})
        rows          = shape.get("rows", 1)
        cols          = shape.get("columns", 1)

        # Estimated raw size = rows × cols × 8 bytes (rough estimate)
        estimated_raw = rows * cols * 8
        compression_ratio = round(estimated_raw / size_bytes, 2) if size_bytes > 0 else 0

        if compression_ratio > 1.5:
            evidence.append(f"File compression ratio ~{compression_ratio}x — storage-efficient.")
        else:
            gaps.append("File is not significantly compressed — storage efficiency low.")

        if not sustainability_info:
            gaps.append("No sustainability information provided in metadata form.")
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=0, rationale="No sustainability information provided.",
                evidence_items=evidence, gaps=gaps, confidence="Low"
            )

        evidence.append("Sustainability information provided.")
        if compression_ratio > 1.5:
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=3, rationale="Carbon footprint acknowledged and storage is optimised.",
                evidence_items=evidence, gaps=gaps, confidence="Low"
            )

        return DomainScoreResult(
            domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
            score=2, rationale="Sustainability info provided but storage not optimised.",
            evidence_items=evidence, gaps=gaps, confidence="Low"
        )


# =============================================================================
# DOMAIN 15 — Continuous Curation & Feedback
# Question: Is the dataset regularly updated with a feedback loop?
# =============================================================================
class CurationScorer(BaseDomainScorer):
    DOMAIN_NUMBER = 15
    DOMAIN_NAME   = "Continuous Curation & Feedback"

    def score(self) -> DomainScoreResult:
        evidence = []
        gaps     = []

        version_format       = self.metadata.get("version_format", "none")
        changelog_provided   = self.metadata.get("changelog_provided", False)
        feedback_mechanism   = self.metadata.get("feedback_mechanism_exists", False)
        dataset_version      = self.metadata.get("dataset_version")

        if not dataset_version:
            gaps.append("No version number provided.")
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=0, rationale="Single release with no versioning or feedback mechanism.",
                evidence_items=evidence, gaps=gaps, confidence="High"
            )

        evidence.append(f"Dataset version: {dataset_version}")

        if not changelog_provided:
            gaps.append("No changelog provided — version history unclear.")
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=1, rationale="Version number present but no changelog or feedback channel.",
                evidence_items=evidence, gaps=gaps, confidence="High"
            )

        evidence.append("Changelog provided.")

        if not feedback_mechanism:
            gaps.append("No formal feedback mechanism declared.")
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=2, rationale="Changelog exists but no formal feedback integration.",
                evidence_items=evidence, gaps=gaps, confidence="High"
            )

        evidence.append("Feedback mechanism declared.")

        if version_format == "semantic":
            evidence.append("Semantic versioning format used.")
            return DomainScoreResult(
                domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
                score=4, rationale="Semantic versioning, changelog, and active feedback mechanism.",
                evidence_items=evidence, gaps=gaps, confidence="High"
            )

        return DomainScoreResult(
            domain_number=self.DOMAIN_NUMBER, domain_name=self.DOMAIN_NAME,
            score=3, rationale="Versioned, changelog, and feedback mechanism exist.",
            evidence_items=evidence, gaps=gaps, confidence="High"
        )


# =============================================================================
# REGISTRY — maps domain numbers to their scorer classes
# The orchestrator uses this to run all 15 scorers automatically.
# =============================================================================
DOMAIN_SCORER_REGISTRY = {
    1:  AnnotationScorer,
    2:  MetadataCompletenessScorer,
    3:  DocumentationScorer,
    4:  RepresentativenessScorer,
    5:  InteroperabilityScorer,
    6:  AIReadinessScorer,
    7:  PrivacyScorer,
    8:  SecurityScorer,
    9:  ProvenanceScorer,
    10: EthicsScorer,
    11: SyntheticDataScorer,
    12: StewardshipScorer,
    13: ModelLinkageScorer,
    14: SustainabilityScorer,
    15: CurationScorer,
}
