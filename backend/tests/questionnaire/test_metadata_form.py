"""Pydantic unit tests for MetadataForm model validation."""
import pytest
from datetime import date
from pydantic import ValidationError

from app.schemas.metadata_form import MetadataForm
from tests.questionnaire.conftest import VALID_METADATA


class TestRequiredFields:
    def test_all_required_present(self):
        form = MetadataForm(**VALID_METADATA)
        assert form.dataset_name == VALID_METADATA["dataset_name"]

    def test_missing_dataset_name(self):
        data = {k: v for k, v in VALID_METADATA.items() if k != "dataset_name"}
        with pytest.raises(ValidationError):
            MetadataForm(**data)

    def test_missing_dataset_type(self):
        data = {k: v for k, v in VALID_METADATA.items() if k != "dataset_type"}
        with pytest.raises(ValidationError):
            MetadataForm(**data)

    def test_missing_study_type(self):
        data = {k: v for k, v in VALID_METADATA.items() if k != "study_type"}
        with pytest.raises(ValidationError):
            MetadataForm(**data)

    def test_missing_target_population(self):
        data = {k: v for k, v in VALID_METADATA.items() if k != "target_population"}
        with pytest.raises(ValidationError):
            MetadataForm(**data)

    def test_missing_geographic_coverage(self):
        data = {k: v for k, v in VALID_METADATA.items() if k != "geographic_coverage"}
        with pytest.raises(ValidationError):
            MetadataForm(**data)

    def test_missing_sensitivity_class(self):
        data = {k: v for k, v in VALID_METADATA.items() if k != "sensitivity_class"}
        with pytest.raises(ValidationError):
            MetadataForm(**data)

    def test_missing_standards_used(self):
        data = {k: v for k, v in VALID_METADATA.items() if k != "standards_used"}
        with pytest.raises(ValidationError):
            MetadataForm(**data)

    def test_missing_deidentification_method(self):
        data = {k: v for k, v in VALID_METADATA.items() if k != "deidentification_method"}
        with pytest.raises(ValidationError):
            MetadataForm(**data)

    def test_missing_license_type(self):
        data = {k: v for k, v in VALID_METADATA.items() if k != "license_type"}
        with pytest.raises(ValidationError):
            MetadataForm(**data)

    def test_missing_access_control_method(self):
        data = {k: v for k, v in VALID_METADATA.items() if k != "access_control_method"}
        with pytest.raises(ValidationError):
            MetadataForm(**data)

    def test_consent_type_omitted_uses_default(self):
        data = {k: v for k, v in VALID_METADATA.items() if k != "consent_type"}
        form = MetadataForm(**data)
        assert form.consent_type == "not_applicable"


class TestEnumValues:
    def test_invalid_dataset_type(self):
        data = {**VALID_METADATA, "dataset_type": "invalid"}
        with pytest.raises(ValidationError):
            MetadataForm(**data)

    def test_invalid_study_type(self):
        data = {**VALID_METADATA, "study_type": "invalid"}
        with pytest.raises(ValidationError):
            MetadataForm(**data)

    def test_invalid_geographic_coverage(self):
        data = {**VALID_METADATA, "geographic_coverage": "invalid"}
        with pytest.raises(ValidationError):
            MetadataForm(**data)

    def test_invalid_sex_distribution(self):
        data = {**VALID_METADATA, "sex_distribution": "invalid"}
        with pytest.raises(ValidationError):
            MetadataForm(**data)

    def test_invalid_consent_type(self):
        data = {**VALID_METADATA, "consent_type": "invalid"}
        with pytest.raises(ValidationError):
            MetadataForm(**data)

    def test_invalid_sensitivity_class(self):
        data = {**VALID_METADATA, "sensitivity_class": "invalid"}
        with pytest.raises(ValidationError):
            MetadataForm(**data)

    def test_invalid_version_format(self):
        data = {**VALID_METADATA, "version_format": "invalid"}
        with pytest.raises(ValidationError):
            MetadataForm(**data)

    def test_invalid_location_granularity(self):
        data = {**VALID_METADATA, "location_granularity": "invalid"}
        with pytest.raises(ValidationError):
            MetadataForm(**data)

    def test_invalid_temporal_granularity(self):
        data = {**VALID_METADATA, "temporal_granularity": "invalid"}
        with pytest.raises(ValidationError):
            MetadataForm(**data)

    def test_invalid_annotator_qualifications(self):
        data = {**VALID_METADATA, "annotator_qualifications": "invalid"}
        with pytest.raises(ValidationError):
            MetadataForm(**data)

    def test_invalid_dpdp_compliance_status(self):
        data = {**VALID_METADATA, "dpdp_compliance_status": "invalid"}
        with pytest.raises(ValidationError):
            MetadataForm(**data)


class TestFieldConstraints:
    def test_dataset_name_too_short(self):
        data = {**VALID_METADATA, "dataset_name": "AB"}
        with pytest.raises(ValidationError):
            MetadataForm(**data)

    def test_target_population_too_short(self):
        data = {**VALID_METADATA, "target_population": "Too short"}
        with pytest.raises(ValidationError):
            MetadataForm(**data)

    def test_annotation_methodology_too_short(self):
        data = {**VALID_METADATA, "annotation_methodology": "Too short"}
        with pytest.raises(ValidationError):
            MetadataForm(**data)

    def test_age_range_min_below_zero(self):
        data = {**VALID_METADATA, "age_range_min": -1}
        with pytest.raises(ValidationError):
            MetadataForm(**data)

    def test_age_range_max_above_120(self):
        data = {**VALID_METADATA, "age_range_max": 150}
        with pytest.raises(ValidationError):
            MetadataForm(**data)

    def test_irr_value_below_zero(self):
        data = {**VALID_METADATA, "irr_value": -0.1}
        with pytest.raises(ValidationError):
            MetadataForm(**data)

    def test_irr_value_above_one(self):
        data = {**VALID_METADATA, "irr_value": 1.5}
        with pytest.raises(ValidationError):
            MetadataForm(**data)

    def test_synthetic_data_pct_below_zero(self):
        data = {**VALID_METADATA, "synthetic_data_pct": -1}
        with pytest.raises(ValidationError):
            MetadataForm(**data)

    def test_synthetic_data_pct_above_100(self):
        data = {**VALID_METADATA, "synthetic_data_pct": 150}
        with pytest.raises(ValidationError):
            MetadataForm(**data)

    def test_num_annotators_zero(self):
        data = {**VALID_METADATA, "num_annotators": 0}
        with pytest.raises(ValidationError):
            MetadataForm(**data)


class TestDefaultValues:
    def test_sex_distribution_default(self):
        data = {k: v for k, v in VALID_METADATA.items() if k != "sex_distribution"}
        form = MetadataForm(**data)
        assert form.sex_distribution == "not_specified"

    def test_dq_checks_applied_default(self):
        data = {k: v for k, v in VALID_METADATA.items() if k != "dq_checks_applied"}
        form = MetadataForm(**data)
        assert form.dq_checks_applied == []

    def test_rare_condition_flag_default(self):
        data = {k: v for k, v in VALID_METADATA.items() if k != "rare_condition_flag"}
        form = MetadataForm(**data)
        assert form.rare_condition_flag is False

    def test_differential_privacy_applied_default(self):
        data = {k: v for k, v in VALID_METADATA.items() if k != "differential_privacy_applied"}
        form = MetadataForm(**data)
        assert form.differential_privacy_applied is False

    def test_equity_analysis_performed_default(self):
        data = {k: v for k, v in VALID_METADATA.items() if k != "equity_analysis_performed"}
        form = MetadataForm(**data)
        assert form.equity_analysis_performed is False

    def test_version_format_default(self):
        data = {k: v for k, v in VALID_METADATA.items() if k != "version_format"}
        form = MetadataForm(**data)
        assert form.version_format == "none"

    def test_data_dictionary_uploaded_default(self):
        data = {k: v for k, v in VALID_METADATA.items() if k != "data_dictionary_uploaded"}
        form = MetadataForm(**data)
        assert form.data_dictionary_uploaded is False

    def test_consent_type_default(self):
        data = {k: v for k, v in VALID_METADATA.items() if k != "consent_type"}
        form = MetadataForm(**data)
        assert form.consent_type == "not_applicable"


class TestCrossFieldValidators:

    def test_end_date_before_start_date(self):
        data = {**VALID_METADATA, "collection_start_date": "2024-06-01", "collection_end_date": "2024-01-01"}
        with pytest.raises(ValidationError, match="collection_end_date"):
            MetadataForm(**data)

    def test_dates_valid_order(self):
        data = {**VALID_METADATA, "collection_start_date": "2024-01-01", "collection_end_date": "2024-06-01"}
        form = MetadataForm(**data)
        assert str(form.collection_start_date) == "2024-01-01"

    def test_age_range_max_less_than_min(self):
        data = {**VALID_METADATA, "age_range_min": 50, "age_range_max": 10}
        with pytest.raises(ValidationError, match="age_range_max"):
            MetadataForm(**data)

    def test_age_range_valid_order(self):
        data = {**VALID_METADATA, "age_range_min": 10, "age_range_max": 50}
        form = MetadataForm(**data)
        assert form.age_range_max == 50

    def test_future_start_date_rejected(self):
        data = {**VALID_METADATA, "collection_start_date": "2099-01-01", "collection_end_date": "2099-06-01"}
        with pytest.raises(ValidationError, match="future"):
            MetadataForm(**data)

    def test_future_end_date_rejected(self):
        data = {**VALID_METADATA, "collection_end_date": "2099-12-31"}
        with pytest.raises(ValidationError, match="future"):
            MetadataForm(**data)

    def test_extra_fields_forbidden(self):
        data = {**VALID_METADATA, "unknown_field": "should_not_be_accepted"}
        with pytest.raises(ValidationError):
            MetadataForm(**data)

    def test_non_string_consent_type_not_allowed(self):
        data = {**VALID_METADATA, "consent_type": None}
        with pytest.raises(ValidationError):
            MetadataForm(**data)
