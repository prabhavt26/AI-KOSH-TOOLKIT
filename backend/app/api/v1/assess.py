from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_db
from app.api.deps import verify_api_key
from app.schemas.metadata_form import MetadataForm
from app.schemas.assessment import AssessmentSubmitResponse, AssessmentStatusResponse, AssessmentResultResponse
from uuid import UUID
import json

router = APIRouter(prefix="/assess", tags=["assessment"])

@router.post(
    "",
    response_model=AssessmentSubmitResponse,
    status_code=status.HTTP_202_ACCEPTED
)
async def submit_assessment(
    file: UploadFile = File(...),
    metadata: str = Form(...),
    api_key: str = Depends(verify_api_key),
    db: AsyncSession = Depends(get_async_db)
):
    """Submits a dataset file and metadata JSON for async quality assessment."""
    try:
        metadata_dict = json.loads(metadata)
        form_data = MetadataForm(**metadata_dict)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid metadata JSON format: {str(e)}"
        )
    
    # Simple placeholder returning 202 Accepted response
    import uuid
    from datetime import datetime
    new_id = uuid.uuid4()
    
    return AssessmentSubmitResponse(
        assessment_id=new_id,
        status="queued",
        estimated_completion_seconds=180,
        poll_url=f"/api/v1/assess/{new_id}",
        submission_timestamp=datetime.utcnow()
    )

@router.get("/{assessment_id}", response_model=AssessmentStatusResponse)
async def get_assessment_status(
    assessment_id: UUID,
    api_key: str = Depends(verify_api_key),
    db: AsyncSession = Depends(get_async_db)
):
    """Checks the status of an active or completed assessment."""
    from datetime import datetime
    return AssessmentStatusResponse(
        assessment_id=assessment_id,
        status="queued",
        submission_timestamp=datetime.utcnow()
    )

