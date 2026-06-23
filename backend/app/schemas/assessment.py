from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict, Any
from datetime import datetime
from uuid import UUID

class AssessmentSubmitResponse(BaseModel):
    assessment_id: UUID
    status: str = "queued"
    estimated_completion_seconds: int = 180
    poll_url: str
    submission_timestamp: datetime

class AssessmentStatusResponse(BaseModel):
    assessment_id: UUID
    status: Literal["queued", "processing", "complete", "failed"]
    dataset_id: Optional[str] = None
    submission_timestamp: datetime
    completion_timestamp: Optional[datetime] = None
    error_message: Optional[str] = None


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
    differential_privacy_applied: bool
    epsilon: Optional[float] = None

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
    json_url: str = Field(..., alias="json")
    html_url: str = Field(..., alias="html")
    pdf_url: str = Field(..., alias="pdf")

    class Config:
        populate_by_name = True

class AssessmentResultResponse(BaseModel):
    assessment_id: UUID
    status: str = "complete"
    dataset_id: Optional[str] = None
    dataset_name: str
    toolkit_version: str
    computed_at: datetime
    domain_11_applicable: bool
    cqi: CQIResult
    prs: PRSResult
    release: ReleaseClassification
    domain_scores: List[DomainScoreObject]
    profile_summary: ProfileSummary
    report_urls: ReportURLs
    audit_log_id: UUID
