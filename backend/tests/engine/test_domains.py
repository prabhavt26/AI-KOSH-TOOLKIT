from app.engine.domains.domain_01_annotation import AnnotationReliabilityScorer
from app.engine.domains.domain_02_metadata import MetadataCompletenessScorer
from app.engine.domains.domain_03_documentation import DocumentationScorer
from app.engine.domains.domain_04_representativeness import RepresentativenessScorer
from app.engine.domains.domain_05_interoperability import InteroperabilityScorer
from app.engine.domains.domain_06_ai_readiness import AIReadinessScorer
from app.engine.domains.domain_07_privacy import PrivacyScorer
from app.engine.domains.domain_08_security import SecurityScorer
from app.engine.domains.domain_09_provenance import ProvenanceScorer
from app.engine.domains.domain_10_ethics import EthicsScorer
from app.engine.domains.domain_11_synthetic import SyntheticDataScorer
from app.engine.domains.domain_12_stewardship import StewardshipScorer
from app.engine.domains.domain_13_model_linkage import ModelLinkageScorer
from app.engine.domains.domain_14_sustainability import SustainabilityScorer
from app.engine.domains.domain_15_curation import CurationScorer

def test_domain_01_annotation():
    criteria = {}
    
    # Score 0: No annotation methodology
    metadata = {}
    scorer = AnnotationReliabilityScorer({}, metadata, criteria)
    assert scorer.score().score == 1

    # Score 1: Annotation documented but no IRR
    metadata = {"annotation_methodology": "Manual labeling"}
    scorer = AnnotationReliabilityScorer({}, metadata, criteria)
    assert scorer.score().score == 1

    # Score 2: IRR < 0.6
    metadata = {"annotation_methodology": "Manual", "irr_value": 0.5, "num_annotators": 2}
    scorer = AnnotationReliabilityScorer({}, metadata, criteria)
    assert scorer.score().score == 2

    # Score 3: IRR >= 0.6, 2 annotators, no credentials
    metadata = {"annotation_methodology": "Manual", "irr_value": 0.7, "num_annotators": 2}
    scorer = AnnotationReliabilityScorer({}, metadata, criteria)
    assert scorer.score().score == 3

    # Score 4: IRR >= 0.8, 2 annotators, credentials
    metadata = {
        "annotation_methodology": "Manual",
        "irr_value": 0.85,
        "num_annotators": 2,
        "annotator_qualifications": "MDs"
    }
    scorer = AnnotationReliabilityScorer({}, metadata, criteria)
    assert scorer.score().score == 4

def test_domain_02_metadata():
    criteria = {}
    # Key fields: dataset_name, dataset_version, dataset_type, study_type, target_population,
    # geographic_coverage, collection_start_date, deidentification_method, standards_used, license_type (10 fields)
    
    # Score 1: < 30% populated
    metadata = {"dataset_name": "Test"}
    scorer = MetadataCompletenessScorer({}, metadata, criteria)
    assert scorer.score().score == 1

    # Score 2: 30% - 59% populated (e.g. 4 fields)
    metadata = {
        "dataset_name": "Test",
        "dataset_version": "1.0",
        "dataset_type": "tabular",
        "study_type": "RCT"
    }
    scorer = MetadataCompletenessScorer({}, metadata, criteria)
    assert scorer.score().score == 2

    # Score 3: 60% - 84% populated (e.g. 7 fields)
    metadata = {
        "dataset_name": "Test",
        "dataset_version": "1.0",
        "dataset_type": "tabular",
        "study_type": "RCT",
        "target_population": "Adults",
        "geographic_coverage": "national",
        "collection_start_date": "2026-01-01"
    }
    scorer = MetadataCompletenessScorer({}, metadata, criteria)
    assert scorer.score().score == 3

    # Score 4: >= 85% populated
    metadata = {
        "dataset_name": "Test",
        "dataset_version": "1.0",
        "dataset_type": "tabular",
        "study_type": "RCT",
        "target_population": "Adults",
        "geographic_coverage": "national",
        "collection_start_date": "2026-01-01",
        "deidentification_method": "HIPAA Safe Harbor",
        "standards_used": "FHIR",
        "license_type": "MIT"
    }
    scorer = MetadataCompletenessScorer({}, metadata, criteria)
    assert scorer.score().score == 4

def test_domain_03_documentation():
    criteria = {}
    metadata = {}
    # 4 items: data_dictionary_uploaded, ethics_approval_ref, consent_type, github_repo_url
    
    scorer = DocumentationScorer({}, metadata, criteria)
    assert scorer.score().score == 1

    metadata = {"data_dictionary_uploaded": True, "ethics_approval_ref": "ETH-123"}
    scorer = DocumentationScorer({}, metadata, criteria)
    assert scorer.score().score == 2

    metadata = {
        "data_dictionary_uploaded": True,
        "ethics_approval_ref": "ETH-123",
        "consent_type": "written",
        "github_repo_url": "http://github.com"
    }
    scorer = DocumentationScorer({}, metadata, criteria)
    assert scorer.score().score == 4

def test_domain_04_representativeness():
    criteria = {}
    metadata = {}
    
    # Score 1: single site / undeclared
    scorer = RepresentativenessScorer({}, metadata, criteria)
    assert scorer.score().score == 1

    # Score 2: village/district or sites > 1
    metadata = {"geographic_coverage": "village", "num_sites": 1}
    scorer = RepresentativenessScorer({}, metadata, criteria)
    assert scorer.score().score == 2

    # Score 3: state/region with >= 3 sites
    metadata = {"geographic_coverage": "state", "num_sites": 3}
    scorer = RepresentativenessScorer({}, metadata, criteria)
    assert scorer.score().score == 3

    # Score 4: national coverage, >= 5 sites, sex distribution reported
    metadata = {
        "geographic_coverage": "national",
        "num_sites": 5,
        "sex_distribution": "M:50%, F:50%"
    }
    scorer = RepresentativenessScorer({}, metadata, criteria)
    assert scorer.score().score == 4

def test_domain_05_interoperability():
    criteria = {}
    # Score 0: < 50% completeness
    profile = {"completeness": {"overall_pct": 45.0}}
    scorer = InteroperabilityScorer(profile, {}, criteria)
    assert scorer.score().score == 1

    # Score 1: 50% to 74.9% completeness
    profile = {"completeness": {"overall_pct": 60.0}}
    scorer = InteroperabilityScorer(profile, {}, criteria)
    assert scorer.score().score == 1

    # Score 2: 75% to 89.9% completeness
    profile = {"completeness": {"overall_pct": 80.0}}
    scorer = InteroperabilityScorer(profile, {}, criteria)
    assert scorer.score().score == 2

    # Score 3: >= 90% completeness, no standards
    profile = {
        "completeness": {"overall_pct": 95.0},
        "standards_detected": {}
    }
    scorer = InteroperabilityScorer(profile, {}, criteria)
    assert scorer.score().score == 3

    # Score 4: >= 90% completeness, standards present
    profile = {
        "completeness": {"overall_pct": 95.0},
        "standards_detected": {"icd_codes_present": True}
    }
    scorer = InteroperabilityScorer(profile, {}, criteria)
    assert scorer.score().score == 4

def test_domain_06_ai_readiness():
    criteria = {}
    profile = {"file": {"format": "csv"}}
    
    # Score 1: Proprietary format (e.g. pdf)
    bad_profile = {"file": {"format": "pdf"}}
    scorer = AIReadinessScorer(bad_profile, {}, criteria)
    assert scorer.score().score == 1

    # Score 2: CSV but no data dictionary
    scorer = AIReadinessScorer(profile, {}, criteria)
    assert scorer.score().score == 2

    # Score 3: CSV + dictionary, but no pipeline
    metadata = {"data_dictionary_uploaded": True}
    scorer = AIReadinessScorer(profile, metadata, criteria)
    assert scorer.score().score == 3

    # Score 4: CSV + dictionary + pipeline
    metadata = {"data_dictionary_uploaded": True, "provenance_pipeline_available": True}
    scorer = AIReadinessScorer(profile, metadata, criteria)
    assert scorer.score().score == 4

def test_domain_07_privacy():
    criteria = {}
    
    # Score 0: Direct identifiers detected
    profile = {"pii_scan": {"direct_identifiers_detected": True}}
    scorer = PrivacyScorer(profile, {}, criteria)
    assert scorer.score().score == 1

    # Score 1: De-identification absent
    profile = {"pii_scan": {"direct_identifiers_detected": False}}
    scorer = PrivacyScorer(profile, {}, criteria)
    assert scorer.score().score == 1

    # Score 2: De-identification only
    metadata = {"deidentification_method": "anonymized"}
    scorer = PrivacyScorer(profile, metadata, criteria)
    assert scorer.score().score == 2

    # Score 3: k-anonymity verified with k=5
    metadata = {"deidentification_method": "anonymized", "k_anonymity_value": 5}
    scorer = PrivacyScorer(profile, metadata, criteria)
    assert scorer.score().score == 3

    # Score 4: DP applied or k-anonymity >= 10
    metadata = {"deidentification_method": "anonymized", "differential_privacy_applied": True}
    scorer = PrivacyScorer(profile, metadata, criteria)
    assert scorer.score().score == 4

def test_domain_08_security():
    criteria = {}
    
    # Score 1: No access control
    scorer = SecurityScorer({}, {}, criteria)
    assert scorer.score().score == 1

    # Score 2: Public
    metadata = {"access_control_method": "Public"}
    scorer = SecurityScorer({}, metadata, criteria)
    assert scorer.score().score == 2

    # Score 3: DUA + request
    metadata = {"access_control_method": "approval required", "dua_required": True}
    scorer = SecurityScorer({}, metadata, criteria)
    assert scorer.score().score == 3

    # Score 4: RBAC
    metadata = {"access_control_method": "role-based access control with approval", "dua_required": True}
    scorer = SecurityScorer({}, metadata, criteria)
    assert scorer.score().score == 4

def test_domain_09_provenance():
    criteria = {}
    
    scorer = ProvenanceScorer({}, {}, criteria)
    assert scorer.score().score == 1

    metadata = {"version_format": "semver"}
    scorer = ProvenanceScorer({}, metadata, criteria)
    assert scorer.score().score == 2

    metadata = {"provenance_pipeline_available": True}
    scorer = ProvenanceScorer({}, metadata, criteria)
    assert scorer.score().score == 3

    metadata = {"provenance_pipeline_available": True, "changelog_provided": True, "version_format": "semver"}
    scorer = ProvenanceScorer({}, metadata, criteria)
    assert scorer.score().score == 4

def test_domain_10_ethics():
    criteria = {}
    
    scorer = EthicsScorer({}, {}, criteria)
    assert scorer.score().score == 1

    metadata = {"ethics_approval_ref": "ETHIC-55"}
    scorer = EthicsScorer({}, metadata, criteria)
    assert scorer.score().score == 1

    metadata = {"ethics_approval_ref": "ETHIC-55", "consent_type": "written"}
    scorer = EthicsScorer({}, metadata, criteria)
    assert scorer.score().score == 2

    metadata = {"ethics_approval_ref": "ETHIC-55", "consent_type": "written", "equity_analysis_performed": True}
    scorer = EthicsScorer({}, metadata, criteria)
    assert scorer.score().score == 3

    metadata = {
        "ethics_approval_ref": "ETHIC-55",
        "consent_type": "written",
        "equity_analysis_performed": True,
        "redressal_mechanism_exists": True
    }
    scorer = EthicsScorer({}, metadata, criteria)
    assert scorer.score().score == 4

def test_domain_11_synthetic():
    criteria = {}
    
    # Score None, N/A if synthetic_data_pct is 0 or None
    metadata = {}
    scorer = SyntheticDataScorer({}, metadata, criteria)
    res = scorer.score()
    assert res.score is None
    assert res.not_applicable is True

    # Score 1: synthetic pct > 0, but no utility/privacy tested
    metadata = {"synthetic_data_pct": 10.0}
    scorer = SyntheticDataScorer({}, metadata, criteria)
    assert scorer.score().score == 1

    # Score 2: utility evaluated
    metadata = {"synthetic_data_pct": 10.0, "synthetic_utility_evaluated": True}
    scorer = SyntheticDataScorer({}, metadata, criteria)
    assert scorer.score().score == 2

    # Score 3: utility + privacy evaluated, pct < 50
    metadata = {"synthetic_data_pct": 10.0, "synthetic_utility_evaluated": True, "synthetic_privacy_tested": True}
    scorer = SyntheticDataScorer({}, metadata, criteria)
    assert scorer.score().score == 3

    # Score 4: utility + privacy evaluated, pct >= 50
    metadata = {"synthetic_data_pct": 60.0, "synthetic_utility_evaluated": True, "synthetic_privacy_tested": True}
    scorer = SyntheticDataScorer({}, metadata, criteria)
    assert scorer.score().score == 4

def test_domain_12_stewardship():
    criteria = {}
    
    scorer = StewardshipScorer({}, {}, criteria)
    assert scorer.score().score == 1

    metadata = {"named_steward_exists": True}
    scorer = StewardshipScorer({}, metadata, criteria)
    assert scorer.score().score == 2

    metadata = {"named_steward_exists": True, "dpdp_compliance_status": "partially_compliant"}
    scorer = StewardshipScorer({}, metadata, criteria)
    assert scorer.score().score == 3

    metadata = {"named_steward_exists": True, "dpdp_compliance_status": "fully_compliant"}
    scorer = StewardshipScorer({}, metadata, criteria)
    assert scorer.score().score == 4

def test_domain_13_model_linkage():
    criteria = {}
    
    scorer = ModelLinkageScorer({}, {}, criteria)
    assert scorer.score().score == 3

    metadata = {"linked_model_ids": []}
    scorer = ModelLinkageScorer({}, metadata, criteria)
    assert scorer.score().score == 3

    metadata = {"linked_model_ids": ["model-1"]}
    scorer = ModelLinkageScorer({}, metadata, criteria)
    assert scorer.score().score == 3

    metadata = {"linked_model_ids": ["model-1", "model-2"]}
    scorer = ModelLinkageScorer({}, metadata, criteria)
    assert scorer.score().score == 4

def test_domain_14_sustainability():
    criteria = {}
    
    # Score 3: Parquet format
    profile = {"file": {"format": "parquet", "size_bytes": 50000000}}
    scorer = SustainabilityScorer(profile, {}, criteria)
    assert scorer.score().score == 3

    # Score 3: Small file format
    profile = {"file": {"format": "csv", "size_bytes": 5000000}}
    scorer = SustainabilityScorer(profile, {}, criteria)
    assert scorer.score().score == 3

    # Score 2: Large CSV
    profile = {"file": {"format": "csv", "size_bytes": 50000000}}
    scorer = SustainabilityScorer(profile, {}, criteria)
    assert scorer.score().score == 2

def test_domain_15_curation():
    criteria = {}
    
    scorer = CurationScorer({}, {}, criteria)
    assert scorer.score().score == 1

    metadata = {"github_repo_url": "http://github.com"}
    scorer = CurationScorer({}, metadata, criteria)
    assert scorer.score().score == 2

    metadata = {"changelog_provided": True}
    scorer = CurationScorer({}, metadata, criteria)
    assert scorer.score().score == 3

    metadata = {"github_repo_url": "http://github.com", "changelog_provided": True}
    scorer = CurationScorer({}, metadata, criteria)
    assert scorer.score().score == 4
