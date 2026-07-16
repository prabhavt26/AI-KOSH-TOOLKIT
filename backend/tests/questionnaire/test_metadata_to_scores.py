"""E2E tests: metadata variations propagate to domain scores correctly.
Requires full stack (workers, S3) running. Marked @pytest.mark.e2e.
Run: docker exec tkt_backend pytest -v -m e2e tests/questionnaire/
"""
import pytest
import time
import httpx
import os

from httpx import AsyncClient, ASGITransport
from app.main import app
from tests.questionnaire.conftest import VALID_METADATA

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "engine", "golden", "10row_golden.csv")


@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="module")
async def api_client(api_key_token):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        ac.headers.update({"Authorization": f"Bearer {api_key_token}", "Content-Type": "application/json"})
        yield ac


async def _upload_file(api_client: AsyncClient) -> str:
    r = await api_client.post("/api/v1/assess/upload-url", json={"filename": "e2e_golden.csv", "file_format": "csv"})
    assert r.status_code in (200, 201), f"Upload URL failed: {r.status_code}"
    data = r.json()
    with open(CSV_PATH, "rb") as f:
        content = f.read()
    async with httpx.AsyncClient() as h:
        ur = await h.put(data["upload_url"], content=content, headers={"Content-Type": "text/csv"})
    assert ur.status_code == 200, f"S3 upload failed: {ur.status_code}"
    return data["file_key"]


async def _submit_and_poll(api_client: AsyncClient, file_key: str, metadata_override: dict) -> dict:
    body = {"file_key": file_key, "metadata": {**VALID_METADATA, **metadata_override}}
    r = await api_client.post("/api/v1/assess", json=body)
    assert r.status_code == 202, f"Submit failed: {r.status_code} {r.text}"
    assess_id = r.json()["assessment_id"]
    for _ in range(60):
        r = await api_client.get(f"/api/v1/assess/{assess_id}")
        assert r.status_code == 200, f"Poll failed: {r.status_code}"
        data = r.json()
        if data.get("status") == "complete":
            return data
        if data.get("status") == "failed":
            pytest.fail(f"Assessment failed: {data.get('error_message', 'unknown')}")
        time.sleep(3)
    pytest.fail("Assessment did not complete within timeout")


@pytest.mark.e2e
@pytest.mark.anyio
class TestSensitivityToPRS:
    async def test_critical_sensitivity_affects_prs(self, api_client: AsyncClient):
        fk = await _upload_file(api_client)
        result = await _submit_and_poll(api_client, fk, {"sensitivity_class": "critical"})
        prs = result.get("prs", {})
        assert prs.get("sensitivity_class") == "critical", f"Expected critical, got {prs.get('sensitivity_class')}"
        assert prs.get("sensitivity_multiplier", 0) >= 1.5, f"Expected multiplier >= 1.5, got {prs.get('sensitivity_multiplier')}"
        assert prs.get("value", 0) > 0, "PRS value should be > 0"


@pytest.mark.e2e
@pytest.mark.anyio
class TestDPToPrivacy:
    async def test_dp_applied_increases_privacy_score(self, api_client: AsyncClient):
        fk_no = await _upload_file(api_client)
        no_dp = await _submit_and_poll(api_client, fk_no, {"differential_privacy_applied": False})
        fk_with = await _upload_file(api_client)
        with_dp = await _submit_and_poll(api_client, fk_with, {"differential_privacy_applied": True})
        s_no = {s["domain_number"]: s["score"] for s in no_dp.get("domain_scores", [])}
        s_with = {s["domain_number"]: s["score"] for s in with_dp.get("domain_scores", [])}
        assert s_with.get(7) is not None, "Privacy domain (7) missing in with-DP"
        assert s_no.get(7) is not None, "Privacy domain (7) missing in no-DP"
        assert s_with[7] >= s_no[7], f"Expected DP ({s_with[7]}) >= no DP ({s_no[7]})"


@pytest.mark.e2e
@pytest.mark.anyio
class TestConsentToEthics:
    async def test_individual_consent_improves_ethics(self, api_client: AsyncClient):
        fk_w = await _upload_file(api_client)
        waiver = await _submit_and_poll(api_client, fk_w, {"consent_type": "waiver"})
        fk_i = await _upload_file(api_client)
        indiv = await _submit_and_poll(api_client, fk_i, {"consent_type": "individual"})
        s_w = {s["domain_number"]: s["score"] for s in waiver.get("domain_scores", [])}
        s_i = {s["domain_number"]: s["score"] for s in indiv.get("domain_scores", [])}
        assert s_w.get(10) is not None, "Ethics domain (10) missing in waiver"
        assert s_i.get(10) is not None, "Ethics domain (10) missing in individual"
        assert s_i[10] >= s_w[10], f"Expected individual ({s_i[10]}) >= waiver ({s_w[10]})"
