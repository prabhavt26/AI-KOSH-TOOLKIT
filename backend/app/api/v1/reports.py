from fastapi import APIRouter, Depends, status, Response
from fastapi.responses import RedirectResponse
from typing import Literal

from app.api.deps import get_user_assessment
from app.models.assessment import Assessment
from app.storage.s3_client import s3_client

router = APIRouter(prefix="/assess", tags=["reports"])

@router.get(
    "/{assessment_id}/report",
    responses={
        401: {"description": "Not authenticated or invalid token"},
        403: {"description": "Access denied / Admin isolation / Not owner"},
        404: {"description": "Assessment not found"}
    }
)
async def download_report(
    format: Literal["json", "html", "pdf"] = "json",
    assessment: Assessment = Depends(get_user_assessment)
):
    """Generates a temporary S3 pre-signed URL to download the report in the requested format."""
    # Enforces BOLA protection and admin boundaries automatically via get_user_assessment
    presigned_url = s3_client.generate_presigned_url(f"reports/{assessment.assessment_id}/report.{format}")
    redirect = RedirectResponse(
        url=presigned_url,
        status_code=status.HTTP_302_FOUND
    )
    redirect.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    redirect.headers["Pragma"] = "no-cache"
    redirect.headers["Expires"] = "0"
    return redirect

