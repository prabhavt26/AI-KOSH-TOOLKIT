import pytest
import uuid
import hashlib
import os
from datetime import date
from httpx import AsyncClient, ASGITransport
from sqlalchemy.future import select

from app.main import app
from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.api_key import ApiKey
from app.api.v1.auth import pwd_context

VALID_METADATA = {
    "dataset_name": "Multi-site TB Cohort Study India 2019-2023",
    "dataset_version": "1.0.0",
    "dataset_type": "tabular",
    "study_type": "cohort",
    "target_population": "Adult patients with confirmed pulmonary TB from 14 RNTCP sites across Maharashtra and Rajasthan",
    "geographic_coverage": "state",
    "age_range_min": 18,
    "age_range_max": 75,
    "sex_distribution": "both",
    "num_sites": 14,
    "collection_start_date": "2024-01-01",
    "collection_end_date": "2024-12-31",
    "annotation_methodology": "Two independent radiologists reviewed all CXR images using a standardized CRF; disagreements resolved by consensus with a third senior radiologist",
    "num_annotators": 3,
    "irr_method": "Cohen's Kappa",
    "irr_value": 0.82,
    "annotator_qualifications": "clinician",
    "dq_checks_applied": [],
    "standards_used": "ICD-10",
    "ethics_approval_ref": "ICMR/IEC/2018/0042",
    "consent_type": "individual",
    "deidentification_method": "HIPAA Safe Harbor",
    "direct_identifiers_present": [],
    "k_anonymity_value": None,
    "location_granularity": "district",
    "temporal_granularity": "month",
    "rare_condition_flag": False,
    "differential_privacy_applied": False,
    "sensitivity_class": "high_stigma",
    "persistent_identifier": "10.5281/zenodo.9876543",
    "license_type": "CC BY-NC 4.0",
    "synthetic_data_pct": 0,
    "synthetic_utility_evaluated": None,
    "synthetic_privacy_tested": None,
    "equity_analysis_performed": False,
    "community_engagement": False,
    "redressal_mechanism_exists": False,
    "dua_required": True,
    "named_steward_exists": False,
    "dpdp_compliance_status": None,
    "access_control_method": "Formal access request process",
    "linked_model_ids": None,
    "data_dictionary_uploaded": True,
    "provenance_pipeline_available": False,
    "github_repo_url": None,
    "changelog_provided": False,
    "version_format": "semantic",
    "sustainability_info_provided": False,
    "feedback_mechanism_exists": False,
    "aikosh_dataset_id": "test-aikosh-001",
    "webhook_url": None,
}

@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="module")
async def api_key_token():
    email = f"qtest_{uuid.uuid4().hex[:8]}@example.com"
    hashed_pwd = pwd_context.hash("TestPass123!")
    plain_key = "tkt_qtest" + uuid.uuid4().hex[:20]
    key_hash = hashlib.sha256(plain_key.encode()).hexdigest()
    async with AsyncSessionLocal() as db:
        user = User(id=uuid.uuid4(), email=email, hashed_password=hashed_pwd, role="user", is_active=True)
        db.add(user)
        await db.flush()
        key = ApiKey(
                key_id=uuid.uuid4(),
                user_id=user.id,
                key_hash=key_hash,
                key_prefix="tkt_qtest",
                owner_name="test-key",
                is_active=True,
            )
        db.add(key)
        await db.commit()
    return plain_key

@pytest.fixture(scope="module")
async def client(api_key_token):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        ac.headers.update({"Authorization": f"Bearer {api_key_token}", "Content-Type": "application/json"})
        yield ac

@pytest.fixture(scope="module")
async def no_auth_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        ac.headers.update({"Content-Type": "application/json"})
        yield ac
