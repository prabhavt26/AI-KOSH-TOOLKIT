import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4, UUID
from datetime import datetime, timezone
import json

from app.models.user import User
from app.models.assessment import Assessment
from app.models.dataset_metadata import DatasetMetadata
from app.models.dataset_profile import DatasetProfile
from app.models.domain_score import DomainScore
from app.models.assessment_result import AssessmentResult
from app.models.audit_log import AuditLog

from app.worker.tasks import run_assessment

@pytest.fixture
def create_test_user(db_session):
    """Creates a temporary user for BOLA/ownership checks."""
    user = User(
        email=f"test_pipeline_{uuid4().hex[:6]}@example.com",
        hashed_password="hashed_password",
        role="user",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@patch("app.worker.tasks.s3_client")
@patch("app.worker.tasks.send_webhook")
def test_run_assessment_pipeline_success(mock_send_webhook, mock_s3_client, db_session, create_test_user):
    # Setup S3 client mock
    mock_s3_client.download_file.return_value = b"name,age,sex\nAlice,30,F\nBob,40,M"
    mock_s3_client.upload_file.return_value = "s3://mock-bucket/file"

    assessment_id = uuid4()
    file_key = f"uploads/{assessment_id}/test_data.csv"

    # Create Assessment DB record
    assessment = Assessment(
        assessment_id=assessment_id,
        dataset_id=f"dataset_{uuid4().hex[:12]}",
        user_id=create_test_user.id,
        status="queued",
        toolkit_version="1.1.0",
        domain_11_applicable=False,
        file_format="csv",
        file_size_bytes=100,
        s3_file_key=file_key
    )
    db_session.add(assessment)

    metadata = DatasetMetadata(
        assessment_id=assessment_id,
        dataset_name="Test pipeline run",
        sensitivity_class="standard",
        location_granularity="district",
        rare_condition_flag=False,
        differential_privacy_applied=False
    )
    db_session.add(metadata)
    db_session.commit()

    # Call Celery task synchronously
    result = run_assessment(str(assessment_id), file_key, {})

    assert result["status"] == "complete"
    assert result["assessment_id"] == str(assessment_id)

    # Refresh objects from DB
    db_session.expire_all()
    
    updated_assessment = db_session.query(Assessment).filter(Assessment.assessment_id == assessment_id).first()
    assert updated_assessment.status == "complete"
    assert updated_assessment.completion_timestamp is not None

    # Verify Profile was written
    profile_rec = db_session.query(DatasetProfile).filter(DatasetProfile.assessment_id == assessment_id).first()
    assert profile_rec is not None
    assert profile_rec.profile_json["shape"]["rows"] == 2
    assert profile_rec.profile_json["shape"]["columns"] == 3

    # Verify 15 domain scores exist
    scores = db_session.query(DomainScore).filter(DomainScore.assessment_id == assessment_id).all()
    assert len(scores) == 15
    expected_scores = {
        1: 1, 2: 1, 3: 1, 4: 1, 5: 3, 6: 2, 7: 1, 8: 1, 9: 1, 10: 1,
        11: None, 12: 1, 13: 3, 14: 3, 15: 1
    }
    for s in scores:
        assert s.score == expected_scores[s.domain_number]
        if s.domain_number == 11:
            assert s.not_applicable is True
        else:
            assert s.not_applicable is False

    # Verify AssessmentResult
    result_rec = db_session.query(AssessmentResult).filter(AssessmentResult.assessment_id == assessment_id).first()
    assert result_rec is not None
    assert result_rec.cqi_band == "Bronze"
    assert result_rec.prs_band == "High"

    assert result_rec.release_classification == "Restricted"

    # Verify AuditLogs
    audit_logs = db_session.query(AuditLog).filter(AuditLog.assessment_id == assessment_id).all()
    event_types = [log.event_type for log in audit_logs]
    assert "assessment_started" in event_types
    assert "assessment_complete" in event_types

    # Verify Webhook dispatched
    mock_send_webhook.delay.assert_called_once()
