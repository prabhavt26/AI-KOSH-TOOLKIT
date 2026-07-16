"""Golden dataset tests for the scoring engine.
Uses an 11-row slice of Electric Sheep Africa TB screening dataset.
Expected values are hand-traced from scorer source code.
"""
import json, os, sys, pytest, yaml
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from app.engine.profiler.profiler import DatasetProfiler
from app.engine.scoring.cqi import compute_cqi
from app.engine.scoring.prs import compute_prs
from app.engine.scoring.release_classifier import ReleaseClassificationEngine
from app.engine.domains import DOMAIN_SCORERS

GOLDEN_DIR = os.path.dirname(__file__)
CSV_PATH   = os.path.join(GOLDEN_DIR, "10row_golden.csv")
CRITERIA_PATH = os.path.join(GOLDEN_DIR, "../../../config/domain_criteria.yaml")

# ---------------------------------------------------------------------------
# Metadata form (52 fields from Questionnaire.md) — TB screening context
# ---------------------------------------------------------------------------
METADATA = {
    "dataset_name": "Synthetic TB Screening Dataset (Golden 11-row)",
    "dataset_version": "1.0.0",
    "dataset_type": "tabular",
    "study_type": "observational",
    "target_population": "Synthetic patients undergoing TB screening at LMIC health facilities",
    "geographic_coverage": "district",
    "age_range_min": 16,
    "age_range_max": 65,
    "sex_distribution": "both",
    "num_sites": 1,
    "collection_start_date": "2024-01-01",
    "collection_end_date": "2024-12-31",
    "annotation_methodology": None,
    "num_annotators": None,
    "irr_method": None,
    "irr_value": None,
    "annotator_qualifications": None,
    "standards_used": "ICD-10",
    "ethics_approval_ref": "IEC/2024/TB-001",
    "consent_type": "individual",
    "deidentification_method": "HIPAA Safe Harbor",
    "differential_privacy_applied": False,
    "sensitivity_class": "high_stigma",
    "persistent_identifier": None,
    "license_type": "CC BY-NC 4.0",
    "synthetic_data_pct": 0,
    "synthetic_utility_evaluated": None,
    "synthetic_privacy_tested": None,
    "access_control_method": "Formal access request process",
    "linked_model_ids": None,
    "data_dictionary_uploaded": False,
    "provenance_pipeline_available": False,
    "github_repo_url": None,
    "changelog_provided": False,
    "version_format": "none",
    "sustainability_info_provided": False,
    "feedback_mechanism_exists": False,
    "equity_analysis_performed": False,
    "community_engagement": False,
    "redressal_mechanism_exists": False,
    "dua_required": True,
    "named_steward_exists": False,
    "dpdp_compliance_status": None,
    "aikosh_dataset_id": "golden-tb-001",
    "webhook_url": None,
    "location_granularity": "district",
    "temporal_granularity": "month",
    "rare_condition_flag": False,
    "dq_checks_applied": [],
    "k_anonymity_value": None,
}


# ===========================================================================
# FIXTURES
# ===========================================================================

@pytest.fixture(scope="module")
def df():
    return pd.read_csv(CSV_PATH)

@pytest.fixture(scope="module")
def profiler(df):
    size = os.path.getsize(CSV_PATH)
    return DatasetProfiler(df, file_format="csv", size_bytes=size)

@pytest.fixture(scope="module")
def profile(profiler):
    return profiler.profile_dataset()

@pytest.fixture(scope="module")
def criteria():
    with open(CRITERIA_PATH) as f:
        return yaml.safe_load(f).get("domains", {})

@pytest.fixture(scope="module")
def domain_scores(profile, criteria):
    results = {}
    for ScorerClass in DOMAIN_SCORERS:
        d = ScorerClass.DOMAIN_NUMBER
        scorer = ScorerClass(profile, METADATA, criteria.get(str(d), {}))
        results[d] = scorer.score()
    return results


# ===========================================================================
# PROFILER TESTS
# ===========================================================================

class TestProfiler:
    def test_file_info(self, profile):
        fi = profile["file"]
        assert fi["format"] == "csv"
        assert fi["size_bytes"] == os.path.getsize(CSV_PATH)
        assert fi["encoding"] == "UTF-8"

    def test_shape(self, profile):
        s = profile["shape"]
        assert s["rows"] == 11
        assert s["columns"] == 25

    def test_pii_scan(self, profile):
        pii = profile["pii_scan"]
        assert pii["direct_identifiers_detected"] is False
        assert pii["id_columns"] == ["id"]
        assert pii["name_columns"] == []
        assert pii["phone_columns"] == []
        assert pii["gps_columns"] == []
        assert pii["dob_columns"] == []

    def test_completeness(self, profile):
        c = profile["completeness"]
        assert c["overall_pct"] == 97.09
        assert "xpert_rif_resistance" in c["columns_below_90pct"]
        assert "xpert_rif_resistance" in c["columns_below_50pct"]

    def test_duplicates(self, profile):
        d = profile["duplicates"]
        assert d["exact_duplicate_rows"] == 0
        assert d["exact_duplicate_pct"] == 0.0

    def test_standards_detected(self, profile):
        std = profile["standards_detected"]
        assert std["icd_codes_present"] is False
        assert std["icd_columns"] == []
        assert std["snomed_codes_present"] is False
        assert std["fhir_structure"] is False
        assert std["loinc_codes_present"] is False

    def test_split_columns(self, profile):
        sc = profile["split_columns"]
        assert sc["split_column_detected"] is False
        assert sc["fold_column_detected"] is False

    def test_label_columns(self, profile):
        lb = profile["label_columns"]
        assert lb["label_column"] == "treatment_outcome"
        assert lb["binary_label_detected"] is False
        assert lb["imbalance_ratio"] == 8.0
        assert lb["class_distribution"]["not_applicable"] == 8
        assert lb["class_distribution"]["cured"] == 2
        assert lb["class_distribution"]["completed"] == 1

    def test_age_distribution(self, profile):
        ad = profile["age_distribution"]
        assert ad["min"] == 16.0
        assert ad["max"] == 53.0
        assert ad["under_18_pct"] == 27.27
        assert ad["18_to_60_pct"] == 72.73
        assert ad["over_60_pct"] == 0.0

    def test_schema_consistency(self, profile):
        sc = profile["schema_consistency"]
        assert sc["conformant_rows_pct"] == 100.0
        assert sc["schema_violations"] == 0

    def test_column_profiles_exist(self, profile):
        cols = profile["columns"]
        assert len(cols) == 25
        col_names = {c["name"] for c in cols}
        expected_cols = {
            "id", "age_years", "sex", "bmi", "hiv_status",
            "cough_2weeks", "cough_duration_weeks", "fever", "night_sweats",
            "weight_loss", "hemoptysis", "chest_pain", "fatigue",
            "loss_of_appetite", "who_symptom_screen_count", "smear_result",
            "xpert_mtb_detected", "xpert_rif_resistance", "cxr_result",
            "cxr_abnormal", "true_tb_status", "tb_type", "tb_classification",
            "rifampicin_resistant", "treatment_outcome",
        }
        assert col_names == expected_cols


# ===========================================================================
# DOMAIN SCORER TESTS
# ===========================================================================

class TestDomains:
    def test_domain_1_annotation(self, domain_scores):
        r = domain_scores[1]
        assert r.domain_name == "Annotation / Labelling Reliability"
        assert r.score == 1
        assert r.not_applicable is False
        assert r.confidence == "Low"
        assert len(r.gaps) > 0

    def test_domain_2_metadata(self, domain_scores):
        r = domain_scores[2]
        assert r.domain_name == "Metadata Completeness"
        assert r.score == 4
        assert r.confidence == "Low"
        assert len(r.evidence_items) == 10
        assert "Metadata field 'dataset_name' is populated." in r.evidence_items
        assert "Metadata field 'license_type' is populated." in r.evidence_items

    def test_domain_3_documentation(self, domain_scores):
        r = domain_scores[3]
        assert r.domain_name == "Documentation & User Guidance"
        assert r.score == 2
        assert r.confidence == "Low"
        ethics_evidence = [e for e in r.evidence_items if "Ethics approval" in e]
        consent_evidence = [e for e in r.evidence_items if "Consent type" in e]
        assert len(ethics_evidence) == 1
        assert len(consent_evidence) == 1

    def test_domain_4_representativeness(self, domain_scores):
        r = domain_scores[4]
        assert r.domain_name == "Population Representativeness"
        assert r.score == 2
        assert r.confidence == "Low"

    def test_domain_5_interoperability(self, domain_scores):
        r = domain_scores[5]
        assert r.domain_name == "Data Structure & Interoperability"
        assert r.score == 4
        assert r.confidence == "High"

    def test_domain_6_ai_readiness(self, domain_scores):
        r = domain_scores[6]
        assert r.domain_name == "AI / Analytics Readiness"
        assert r.score == 2
        assert r.confidence == "Medium"

    def test_domain_7_privacy(self, domain_scores):
        r = domain_scores[7]
        assert r.domain_name == "Privacy & Identifiability"
        assert r.score == 2
        assert r.confidence == "Medium"

    def test_domain_8_security(self, domain_scores):
        r = domain_scores[8]
        assert r.domain_name == "Security & Access Governance"
        assert r.score == 3
        assert r.confidence == "Low"

    def test_domain_9_provenance(self, domain_scores):
        r = domain_scores[9]
        assert r.domain_name == "Provenance & Workflow Transparency"
        assert r.score == 2
        assert r.confidence == "Low"

    def test_domain_10_ethics(self, domain_scores):
        r = domain_scores[10]
        assert r.domain_name == "Ethical & Social Accountability"
        assert r.score == 2
        assert r.confidence == "Low"

    def test_domain_11_synthetic(self, domain_scores):
        r = domain_scores[11]
        assert r.domain_name == "Synthetic / Simulated Data"
        assert r.score is None
        assert r.not_applicable is True
        assert r.confidence is None

    def test_domain_12_stewardship(self, domain_scores):
        r = domain_scores[12]
        assert r.domain_name == "Stewardship & Governance"
        assert r.score == 1
        assert r.confidence == "Low"

    def test_domain_13_model_linkage(self, domain_scores):
        r = domain_scores[13]
        assert r.domain_name == "Model Linkage Integrity"
        assert r.score == 3
        assert r.confidence == "Low"

    def test_domain_14_sustainability(self, domain_scores):
        r = domain_scores[14]
        assert r.domain_name == "Environmental Sustainability"
        assert r.score == 3
        assert r.confidence == "Medium"

    def test_domain_15_curation(self, domain_scores):
        r = domain_scores[15]
        assert r.domain_name == "Continuous Curation & Feedback"
        assert r.score == 1
        assert r.confidence == "Low"


# ===========================================================================
# CQI / PRS / RELEASE TESTS
# ===========================================================================

class TestCQI:
    def test_cqi_value(self, domain_scores):
        scores = {d: r.score for d, r in domain_scores.items()}
        d11_app = domain_scores[11].score is not None
        result = compute_cqi(scores, d11_app)
        assert result.total_score == 32
        assert result.max_possible == 56
        assert result.cqi == 57.1
        assert result.band == "Silver"
        assert result.domain_11_applicable is False


class TestPRS:
    def test_prs_value(self, profile):
        result = compute_prs(profile, METADATA)
        assert result.baseline_risk == 15.0
        assert result.sensitivity_class == "high_stigma"
        assert result.sensitivity_multiplier == 1.5
        assert result.adjusted_risk == 22.5
        assert result.prs == 23
        assert result.band == "Moderate"


class TestRelease:
    def test_release_classification(self):
        # High-stigma data → Controlled policy override (no DP verified)
        result = ReleaseClassificationEngine.classify_release(
            cqi=50.0,
            prs=23,
            prs_band="Moderate",
            sensitivity_class="high_stigma",
            differential_privacy_verified=False,
        )
        assert result.classification == "Controlled"
        assert result.policy_override_applied is True
        assert "High-stigma data" in result.justification

    def test_release_open_access(self):
        # Gold CQI + Low PRS → Open
        result = ReleaseClassificationEngine.classify_release(
            cqi=85.0, prs=10, prs_band="Low",
            sensitivity_class="standard",
        )
        assert result.classification == "Open"
        assert result.policy_override_applied is False

    def test_release_restricted_high_prs(self):
        result = ReleaseClassificationEngine.classify_release(
            cqi=90.0, prs=50, prs_band="High",
            sensitivity_class="standard",
        )
        assert result.classification == "Restricted"
        assert result.policy_override_applied is False

    def test_release_restricted_high_stigma_high_prs(self):
        # High-stigma + High PRS → Restricted (policy override)
        result = ReleaseClassificationEngine.classify_release(
            cqi=90.0, prs=50, prs_band="High",
            sensitivity_class="high_stigma",
        )
        assert result.classification == "Restricted"
        assert result.policy_override_applied is True

    def test_release_low_cqi_low_prs(self):
        result = ReleaseClassificationEngine.classify_release(
            cqi=30.0, prs=10, prs_band="Low",
            sensitivity_class="standard",
        )
        assert result.classification == "Controlled"
        assert result.policy_override_applied is False
