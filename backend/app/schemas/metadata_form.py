from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from typing import Optional, List, Literal
from datetime import date, timezone

class MetadataForm(BaseModel):
    model_config = ConfigDict(extra='forbid')

    dataset_name: str = Field(..., min_length=5)

    dataset_version: Optional[str] = Field(None, max_length=100)
    dataset_type: Literal["tabular", "imaging", "text", "multimodal"]
    study_type: Literal["RCT", "cohort", "cross_sectional", "registry", "observational", "case_control", "other"]
    target_population: str = Field(..., min_length=20)
    geographic_coverage: Literal["village", "taluk", "district", "state", "national", "multi_country"]
    
    age_range_min: Optional[int] = Field(None, ge=0, le=120)
    age_range_max: Optional[int] = Field(None, ge=0, le=120)
    sex_distribution: Optional[Literal["male_only", "female_only", "both", "not_specified"]] = "not_specified"
    num_sites: Optional[int] = Field(None, ge=1)
    
    collection_start_date: Optional[date] = None
    collection_end_date: Optional[date] = None
    
    annotation_methodology: Optional[str] = Field(None, min_length=50)
    num_annotators: Optional[int] = Field(None, ge=1)
    irr_method: Optional[str] = None
    irr_value: Optional[float] = Field(None, ge=0.0, le=1.0)
    annotator_qualifications: Optional[Literal["clinician", "student", "crowdsourced", "automated", "mixed", "other"]] = None
    
    dq_checks_applied: Optional[List[str]] = Field(default_factory=list)
    
    standards_used: str
    ethics_approval_ref: Optional[str] = None
    consent_type: Literal["individual", "waiver", "community", "not_applicable"] = "not_applicable"
    deidentification_method: str
    
    direct_identifiers_present: Optional[List[str]] = Field(default_factory=list)
    k_anonymity_value: Optional[int] = Field(None, ge=1)
    location_granularity: Optional[Literal["village", "taluk", "district", "state", "national", "multi_country", "none"]] = None
    temporal_granularity: Optional[Literal["day", "month", "year", "not_applicable"]] = None
    rare_condition_flag: bool = False
    
    differential_privacy_applied: bool = False
    
    sensitivity_class: Literal["standard", "high_stigma", "critical"]
    persistent_identifier: Optional[str] = None
    license_type: str
    synthetic_data_pct: Optional[float] = Field(None, ge=0.0, le=100.0)
    synthetic_utility_evaluated: Optional[bool] = None
    synthetic_privacy_tested: Optional[bool] = None
    
    equity_analysis_performed: bool = False
    community_engagement: bool = False
    redressal_mechanism_exists: bool = False
    dua_required: bool = False
    named_steward_exists: bool = False
    dpdp_compliance_status: Optional[Literal["fully_compliant", "partially_compliant", "not_compliant", "not_applicable"]] = None
    
    access_control_method: str
    linked_model_ids: Optional[List[str]] = Field(default_factory=list)
    data_dictionary_uploaded: bool = False
    provenance_pipeline_available: bool = False
    github_repo_url: Optional[str] = None
    changelog_provided: bool = False
    version_format: Optional[Literal["semantic", "arbitrary", "none"]] = "none"
    sustainability_info_provided: bool = False
    feedback_mechanism_exists: bool = False
    
    aikosh_dataset_id: Optional[str] = None
    webhook_url: Optional[str] = None

    @model_validator(mode="after")
    def validate_dates(self) -> 'MetadataForm':
        if self.collection_start_date and self.collection_end_date:
            if self.collection_end_date < self.collection_start_date:
                raise ValueError("collection_end_date must be on or after collection_start_date")
        return self

    @model_validator(mode="after")
    def validate_age_range(self) -> 'MetadataForm':
        if self.age_range_min is not None and self.age_range_max is not None:
            if self.age_range_max < self.age_range_min:
                raise ValueError("age_range_max must be >= age_range_min")
        return self

    @model_validator(mode="after")
    def validate_future_dates(self) -> 'MetadataForm':
        today = date.today()
        if self.collection_start_date and self.collection_start_date > today:
            raise ValueError("collection_start_date cannot be in the future")
        if self.collection_end_date and self.collection_end_date > today:
            raise ValueError("collection_end_date cannot be in the future")
        return self
