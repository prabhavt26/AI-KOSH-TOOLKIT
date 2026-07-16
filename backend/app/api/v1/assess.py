import json
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Union
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_async_db
from app.api.deps import get_current_user, get_user_assessment, get_current_active_reviewer
from app.models.user import User
from app.models.assessment import Assessment
from app.models.audit_log import AuditLog
from app.models.dataset_metadata import DatasetMetadata
from app.schemas.metadata_form import MetadataForm
from app.schemas.assessment import (
    AssessmentSubmitResponse, 
    AssessmentStatusResponse, 
    AssessmentResultResponse,
    UploadUrlRequest, 
    UploadUrlResponse,
    AssessmentSubmitRequest,
    CQIResult,
    PRSResult,
    ReleaseClassification,
    ProfileSummary,
    ReportURLs,
    DomainScoreObject,
    AuditLogItemResponse
)
from app.storage.s3_client import s3_client
from app.worker.tasks import run_assessment
from app.audit.logger import audit_logger


router = APIRouter(prefix="/assess", tags=["assessment"])

ALLOWED_EXTENSIONS = {"csv", "xlsx", "parquet", "json", "tsv", "zip", "pdf", "py", "r", "ipynb", "dcm"}

@router.post(
    "/upload-url",
    response_model=UploadUrlResponse,
    status_code=status.HTTP_201_CREATED
)
async def generate_upload_url(
    req: UploadUrlRequest,
    current_user: User = Depends(get_current_user)
):
    """Generates a pre-signed S3 upload URL for direct client-to-S3 upload."""
    ext = req.filename.split(".")[-1].lower() if "." in req.filename else req.file_format.lower()
    if ext not in ALLOWED_EXTENSIONS or req.file_format.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported file format or extension '.{ext}'. Allowed formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    assessment_id = uuid.uuid4()
    file_key = f"uploads/{assessment_id}/{req.filename}"
    upload_url = s3_client.generate_presigned_upload_url(file_key)
    return UploadUrlResponse(
        upload_url=upload_url,
        file_key=file_key,
        assessment_id=assessment_id
    )

@router.post(
    "",
    response_model=AssessmentSubmitResponse,
    status_code=status.HTTP_202_ACCEPTED
)
async def submit_assessment(
    request: Request,
    req: AssessmentSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Submits a dataset for assessment after the file(s) have been uploaded to S3."""
    
    if not s3_client.file_exists(req.file_key):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Main dataset file not found in S3. Please upload first."
        )

    try:
        assessment_id = UUID(req.file_key.split("/")[1])
    except (IndexError, ValueError):
        assessment_id = uuid.uuid4()

    dataset_id = req.metadata.aikosh_dataset_id or f"dataset_{uuid.uuid4().hex[:12]}"
    api_key_id = getattr(request.state, "api_key_id", None)
    
    # We infer domain 11 applicability if synthetic_data_pct > 0 or if not explicitly None
    domain_11_app = False
    if req.metadata.synthetic_data_pct is not None and req.metadata.synthetic_data_pct > 0:
        domain_11_app = True
        
    new_assessment = Assessment(
        assessment_id=assessment_id,
        dataset_id=dataset_id,
        user_id=current_user.id,
        api_key_id=api_key_id,
        status="queued",
        toolkit_version="1.1.0",
        domain_11_applicable=domain_11_app,
        assessment_mode="full",
        file_format=req.file_key.split(".")[-1] if "." in req.file_key else "csv",
        file_size_bytes=0, 
        s3_file_key=req.file_key,
        submission_timestamp=datetime.now(timezone.utc)
    )
    db.add(new_assessment)

    form_dict = req.metadata.model_dump(exclude_unset=True)
    form_dict["assessment_id"] = assessment_id
    form_dict["raw_form_json"] = req.metadata.model_dump(mode="json")
    
    valid_cols = {c.name for c in DatasetMetadata.__table__.columns}
    insert_dict = {k: v for k, v in form_dict.items() if k in valid_cols}
    
    new_metadata = DatasetMetadata(**insert_dict)
    db.add(new_metadata)

    await db.commit()
    
    await audit_logger.log_event(
        db,
        assessment_id,
        "assessment_submitted",
        {"file_key": req.file_key, "dataset_id": dataset_id},
        "api"
    )

    run_assessment.delay(str(assessment_id), req.file_key, req.metadata.model_dump(mode="json"))

    return AssessmentSubmitResponse(
        assessment_id=assessment_id,
        status="queued",
        estimated_completion_seconds=180,
        poll_url=f"/api/v1/assess/{assessment_id}",
        submitted_at=new_assessment.submission_timestamp
    )

@router.get(
    "/",
    response_model=List[AssessmentStatusResponse],
)
async def list_user_assessments(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Returns a paginated list of the current user's assessments."""
    stmt = select(Assessment).where(Assessment.user_id == current_user.id).order_by(desc(Assessment.submission_timestamp)).offset(skip).limit(limit)
    result = await db.execute(stmt)
    assessments = result.scalars().all()
    
    return [
        AssessmentStatusResponse(
            assessment_id=a.assessment_id,
            status=a.status,
            dataset_id=a.dataset_id,
            submitted_at=a.submission_timestamp,
            completed_at=a.completion_timestamp,
            error_message=a.error_message,
            error_traceback=a.error_traceback
        ) for a in assessments
    ]


@router.get(
    "/{assessment_id}",
    response_model=Union[AssessmentResultResponse, AssessmentStatusResponse],
    responses={
        401: {"description": "Not authenticated or invalid token"},
        403: {"description": "Access denied / Admin isolation / Not owner"},
        404: {"description": "Assessment not found"}
    }
)
async def get_assessment_status_route(
    assessment: Assessment = Depends(get_user_assessment),
    db: AsyncSession = Depends(get_async_db)
):
    """Checks the status of an active or completed assessment, verifying ownership limits."""
    if assessment.status == "complete":
        from sqlalchemy.orm import selectinload
        stmt = select(Assessment).where(Assessment.assessment_id == assessment.assessment_id).options(
            selectinload(Assessment.result),
            selectinload(Assessment.domain_scores),
            selectinload(Assessment.metadata_form),
            selectinload(Assessment.profile),
            selectinload(Assessment.audit_logs)
        )
        res = await db.execute(stmt)
        assessment = res.scalars().first()
        
        if assessment and assessment.result:
            # Build CQIResult
            cqi_obj = CQIResult(
                value=float(assessment.result.cqi),
                band=assessment.result.cqi_band,
                total_score=assessment.result.total_domain_score,
                max_possible=assessment.result.max_possible_score,
                formula_trace=assessment.result.cqi_formula_trace or ""
            )
            
            # Build PRSResult
            metadata_rec = assessment.metadata_form
            sensitivity_class = metadata_rec.sensitivity_class if metadata_rec else "standard"
            
            prs_obj = PRSResult(
                value=int(assessment.result.prs),
                band=assessment.result.prs_band,
                baseline_risk=float(assessment.result.prs_baseline_risk or 0.0),
                sensitivity_class=sensitivity_class,
                sensitivity_multiplier=float(assessment.result.prs_sensitivity_multiplier or 1.0),
                adjusted_risk=float(assessment.result.prs_baseline_risk or 0.0) * float(assessment.result.prs_sensitivity_multiplier or 1.0),
                computation_trace=assessment.result.prs_computation_trace or ""
            )
            
            # Build ReleaseClassification
            release_obj = ReleaseClassification(
                classification=assessment.result.release_classification,
                justification=assessment.result.classification_justification or "",
                policy_override_applied=assessment.result.policy_override_applied
            )
            
            # Build DomainScoreObject list
            domain_scores_objs = []
            for ds in sorted(assessment.domain_scores, key=lambda x: x.domain_number):
                domain_scores_objs.append(DomainScoreObject(
                    domain_number=ds.domain_number,
                    domain_name=ds.domain_name,
                    score=ds.score,
                    max_score=None if ds.not_applicable else 4,
                    not_applicable=ds.not_applicable,
                    confidence=None if ds.not_applicable else ds.confidence_level,
                    rationale=ds.rationale,
                    evidence_items=ds.evidence_items or [],
                    gaps=ds.gaps or []
                ))
                
            # Build ProfileSummary
            profile_json = assessment.profile.profile_json if assessment.profile else {}
            profile_summary = ProfileSummary(
                rows=profile_json.get("shape", {}).get("rows", 0),
                columns=profile_json.get("shape", {}).get("columns", 0),
                file_format=profile_json.get("file", {}).get("format", "csv"),
                file_size_bytes=profile_json.get("file", {}).get("size_bytes", 0),
                overall_completeness_pct=profile_json.get("completeness", {}).get("overall_pct", 100.0),
                direct_identifiers_detected=profile_json.get("pii_scan", {}).get("direct_identifiers_detected", False),
                icd_codes_detected=profile_json.get("standards_detected", {}).get("icd_codes_present", False),
                sampled=profile_json.get("sampled", False),
                sample_rows=profile_json.get("sample_rows", None)
            )
            
            # Build ReportURLs (formatted as gateway endpoint paths for client accessibility)
            report_urls = ReportURLs(
                json=f"/api/v1/assess/{assessment.assessment_id}/report?format=json",
                html=f"/api/v1/assess/{assessment.assessment_id}/report?format=html",
                pdf=f"/api/v1/assess/{assessment.assessment_id}/report?format=pdf"
            )
            
            # Find audit_log_id
            audit_log_id = assessment.assessment_id  # default fallback
            if assessment.audit_logs:
                for log in assessment.audit_logs:
                    if log.event_type == "assessment_complete":
                        audit_log_id = log.log_id
                        break
                else:
                    audit_log_id = assessment.audit_logs[0].log_id
                    
            return AssessmentResultResponse(
                assessment_id=assessment.assessment_id,
                status="complete",
                dataset_id=assessment.dataset_id,
                dataset_name=metadata_rec.dataset_name if metadata_rec else "Unknown",
                toolkit_version=assessment.toolkit_version,
                assessed_at=assessment.result.computed_at or assessment.completion_timestamp or datetime.now(timezone.utc),
                domain_11_applicable=assessment.domain_11_applicable,
                cqi=cqi_obj,
                prs=prs_obj,
                release=release_obj,
                domain_scores=domain_scores_objs,
                profile_summary=profile_summary,
                report_urls=report_urls,
                audit_log_id=audit_log_id
            )

    return AssessmentStatusResponse(
        assessment_id=assessment.assessment_id,
        status=assessment.status,
        dataset_id=assessment.dataset_id,
        submitted_at=assessment.submission_timestamp,
        completed_at=assessment.completion_timestamp,
        error_message=assessment.error_message,
        error_traceback=assessment.error_traceback
    )

@router.get(
    "/{assessment_id}/audit",
    response_model=List[AuditLogItemResponse],
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Forbidden - Reviewer role required"},
        404: {"description": "Assessment not found"}
    }
)
async def get_assessment_audit_logs(
    assessment_id: str,
    reviewer: User = Depends(get_current_active_reviewer),
    assessment: Assessment = Depends(get_user_assessment),
    db: AsyncSession = Depends(get_async_db)
):
    """Returns full audit trail for an assessment (Reviewer or Admin role required)."""
    stmt = select(AuditLog).where(AuditLog.assessment_id == assessment.assessment_id).order_by(AuditLog.event_timestamp.asc())
    result = await db.execute(stmt)
    logs = result.scalars().all()
    return logs


