from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Literal, Dict, Any
from datetime import datetime
from uuid import UUID
from app.schemas.metadata_form import MetadataForm

class UploadUrlRequest(BaseModel):
    filename: str
    file_format: str

class UploadUrlResponse(BaseModel):
    upload_url: str
    file_key: str
    assessment_id: UUID

class AssessmentSubmitRequest(BaseModel):
    file_key: str
    metadata: MetadataForm
    data_dictionary_key: Optional[str] = None
    sop_key: Optional[str] = None
    consent_doc_key: Optional[str] = None
    pipeline_script_key: Optional[str] = None

class AssessmentSubmitResponse(BaseModel):
    assessment_id: UUID
    status: str = "queued"
    estimated_completion_seconds: int = 180
    poll_url: str
    submitted_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AssessmentStatusResponse(BaseModel):
    assessment_id: UUID
    status: Literal["queued", "processing", "complete", "failed"]
    dataset_id: Optional[str] = None
    submitted_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DomainScoreObject(BaseModel):
    domain_number: int
    domain_name: str
    score: Optional[int] = None
    max_score: Optional[int] = 4
    not_applicable: bool = False
    confidence: Optional[Literal["High", "Medium", "Low"]] = None
    rationale: Optional[str] = None
    evidence_items: List[str] = []
    gaps: List[str] = []
    inferred: bool = False


class CQIResult(BaseModel):
    value: float
    band: str
    total_score: int
    max_possible: int
    formula_trace: str

class PRSResult(BaseModel):
    value: int
    band: str
    baseline_risk: float
    sensitivity_class: str
    sensitivity_multiplier: float
    adjusted_risk: float
    computation_trace: str

class ReleaseClassification(BaseModel):
    classification: Literal["Open", "Controlled", "Restricted"]
    justification: str
    policy_override_applied: bool

class ProfileSummary(BaseModel):
    rows: int
    columns: int
    file_format: str
    file_size_bytes: int
    overall_completeness_pct: float
    direct_identifiers_detected: bool
    icd_codes_detected: bool
    sampled: bool
    sample_rows: Optional[int] = None

class ReportURLs(BaseModel):
    json: str
    html: str
    pdf: str

class AssessmentResultResponse(BaseModel):
    assessment_id: UUID
    status: str = "complete"
    dataset_id: Optional[str] = None
    dataset_name: str
    toolkit_version: str
    assessed_at: datetime
    domain_11_applicable: bool
    cqi: CQIResult
    prs: PRSResult
    release: ReleaseClassification
    domain_scores: List[DomainScoreObject]
    profile_summary: ProfileSummary
    report_urls: ReportURLs
    audit_log_id: UUID

class AuditLogItemResponse(BaseModel):
    log_id: UUID
    assessment_id: UUID
    event_type: str
    event_timestamp: datetime
    component: Optional[str] = None
    event_detail: Dict[str, Any] = {}
    severity: str = "INFO"

    model_config = ConfigDict(from_attributes=True)

class AssessmentListItem(BaseModel):
    assessment_id: UUID
    dataset_id: str
    status: str
    submission_timestamp: datetime
    completion_timestamp: Optional[datetime] = None
    cqi: Optional[float] = None
    cqi_band: Optional[str] = None
    prs: Optional[int] = None
    prs_band: Optional[str] = None
    release_classification: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class PaginatedAssessmentListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[AssessmentListItem]


