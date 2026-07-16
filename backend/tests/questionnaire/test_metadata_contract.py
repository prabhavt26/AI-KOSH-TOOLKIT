"""HTTP contract tests for MetadataForm validation through POST /assess."""
import pytest
import uuid
from httpx import AsyncClient

from tests.questionnaire.conftest import VALID_METADATA


VALID_FILE_KEY = f"uploads/{uuid.uuid4()}/test.csv"


@pytest.mark.anyio
class TestValidMetadata:
    async def test_valid_metadata_passes_validation(self, client: AsyncClient):
        body = {"file_key": VALID_FILE_KEY, "metadata": VALID_METADATA}
        r = await client.post("/api/v1/assess", json=body)
        assert r.status_code == 404
        assert "not found in S3" in r.text


@pytest.mark.anyio
class TestInvalidMetadata:
    async def test_bad_enum_value_returns_422(self, client: AsyncClient):
        bad = {**VALID_METADATA, "dataset_type": "invalid_type"}
        body = {"file_key": VALID_FILE_KEY, "metadata": bad}
        r = await client.post("/api/v1/assess", json=body)
        assert r.status_code == 422

    async def test_short_dataset_name_returns_422(self, client: AsyncClient):
        bad = {**VALID_METADATA, "dataset_name": "AB"}
        body = {"file_key": VALID_FILE_KEY, "metadata": bad}
        r = await client.post("/api/v1/assess", json=body)
        assert r.status_code == 422

    async def test_missing_required_field_returns_422(self, client: AsyncClient):
        bad = {k: v for k, v in VALID_METADATA.items() if k != "license_type"}
        body = {"file_key": VALID_FILE_KEY, "metadata": bad}
        r = await client.post("/api/v1/assess", json=body)
        assert r.status_code == 422

    async def test_missing_multiple_required_returns_422(self, client: AsyncClient):
        bad = {k: v for k, v in VALID_METADATA.items() if k not in ("standards_used", "deidentification_method", "access_control_method")}
        body = {"file_key": VALID_FILE_KEY, "metadata": bad}
        r = await client.post("/api/v1/assess", json=body)
        assert r.status_code == 422

    async def test_extra_fields_returns_422(self, client: AsyncClient):
        bad = {**VALID_METADATA, "unknown_field": "should_not_be_accepted"}
        body = {"file_key": VALID_FILE_KEY, "metadata": bad}
        r = await client.post("/api/v1/assess", json=body)
        assert r.status_code == 422

    async def test_age_range_invalid_returns_422(self, client: AsyncClient):
        bad = {**VALID_METADATA, "age_range_min": 80, "age_range_max": 10}
        body = {"file_key": VALID_FILE_KEY, "metadata": bad}
        r = await client.post("/api/v1/assess", json=body)
        assert r.status_code == 422

    async def test_future_date_returns_422(self, client: AsyncClient):
        bad = {**VALID_METADATA, "collection_end_date": "2099-12-31"}
        body = {"file_key": VALID_FILE_KEY, "metadata": bad}
        r = await client.post("/api/v1/assess", json=body)
        assert r.status_code == 422


@pytest.mark.anyio
class TestAuth:
    async def test_no_auth_returns_401(self, no_auth_client: AsyncClient):
        body = {"file_key": VALID_FILE_KEY, "metadata": VALID_METADATA}
        r = await no_auth_client.post("/api/v1/assess", json=body)
        assert r.status_code == 401
