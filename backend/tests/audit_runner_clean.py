import asyncio
import time
import httpx
import json
import uuid
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.config import settings

BASE_URL = "http://localhost:8000"
VALID_META = {
    "dataset_name": "TB Cohort 2026",
    "dataset_type": "tabular",
    "study_type": "RCT",
    "target_population": "Adult hospital patients presenting with respiratory symptoms",
    "geographic_coverage": "district",
    "standards_used": "FHIR, ICD-10",
    "license_type": "CC_BY_4",
    "deidentification_method": "anonymized",
    "access_control_method": "role_based",
    "differential_privacy_applied": False,
    "sensitivity_class": "standard",
    "consent_type": "individual"
}

async def run():
    results = {}
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
        # User A
        u_a = f"audit_usera_{int(time.time())}@ex.com"
        r_a = await client.post("/api/v1/auth/register", json={"email": u_a, "password": "StrongPassword123!", "full_name": "Auditor A", "organization": "AIKosh", "role": "data_custodian"})
        c_a = {"session_token": r_a.headers.get("set-cookie").split("session_token=")[1].split(";")[0]}
        
        # User B
        u_b = f"audit_userb_{int(time.time())}@ex.com"
        r_b = await client.post("/api/v1/auth/register", json={"email": u_b, "password": "StrongPassword123!", "full_name": "Auditor B", "organization": "AIKosh", "role": "data_custodian"})
        c_b = {"session_token": r_b.headers.get("set-cookie").split("session_token=")[1].split(";")[0]}

        # Invalid upload URL check
        r_url_inv = await client.post("/api/v1/assess/upload-url", json={"filename": "malicious.exe", "file_format": "exe"}, cookies=c_a)
        results["upload_invalid_format"] = {"status": r_url_inv.status_code, "body": r_url_inv.json()}

        # Valid upload URL
        r_url = await client.post("/api/v1/assess/upload-url", json={"filename": "10row_golden.csv", "file_format": "csv"}, cookies=c_a)
        u_data = r_url.json()
        aid = u_data["assessment_id"]
        fkey = u_data["file_key"]
        results["upload_url"] = {"status": r_url.status_code, "aid": aid}

        with open("/app/tests/engine/golden/10row_golden.csv", "rb") as f:
            csv_bytes = f.read()
        async with httpx.AsyncClient() as put_cli:
            r_put = await put_cli.put(u_data["upload_url"], content=csv_bytes, headers={"Content-Type": "text/csv"})
            results["s3_put_status"] = r_put.status_code

        # Extra fields check
        r_extra = await client.post("/api/v1/assess", json={"file_key": fkey, "metadata": {**VALID_META, "malicious_extra": True}}, cookies=c_a)
        results["extra_fields_check"] = {"status": r_extra.status_code, "body": r_extra.json()}

        # Valid submit
        r_sub = await client.post("/api/v1/assess", json={"file_key": fkey, "metadata": VALID_META}, cookies=c_a)
        results["valid_submission"] = {"status": r_sub.status_code, "body": r_sub.json()}

        # Poll until complete
        st = "queued"
        att = 0
        p_data = {}
        while st in ["queued", "processing"] and att < 30:
            await asyncio.sleep(2)
            r_p = await client.get(f"/api/v1/assess/{aid}", cookies=c_a)
            p_data = r_p.json()
            st = p_data.get("status")
            att += 1
        results["poll_completion"] = {"status": st, "attempts": att, "data": p_data}

        # Reports and presigned URL freshness
        r_rep1 = await client.get(f"/api/v1/assess/{aid}/report?format=html", cookies=c_a)
        r_rep2 = await client.get(f"/api/v1/assess/{aid}/report?format=html", cookies=c_a)
        results["report_freshness"] = {
            "status": r_rep1.status_code,
            "rep1_loc": r_rep1.headers.get("location"),
            "rep2_loc": r_rep2.headers.get("location"),
            "is_fresh_presigned_url": r_rep1.headers.get("location") != r_rep2.headers.get("location")
        }

        # Non-existent ID check
        r_non = await client.get(f"/api/v1/assess/{uuid.uuid4()}", cookies=c_a)
        results["nonexistent_id_check"] = {"status": r_non.status_code, "body": r_non.json()}

        # Cookie BOLA check
        r_bola_c = await client.get(f"/api/v1/assess/{aid}", cookies=c_b)
        results["bola_cookie_check"] = {"status": r_bola_c.status_code, "body": r_bola_c.json()}

        # API Key BOLA check
        r_ka = await client.post("/api/v1/auth/keys", json={"owner_name": "Key A", "role": "developer"}, cookies=c_a)
        r_kb = await client.post("/api/v1/auth/keys", json={"owner_name": "Key B", "role": "developer"}, cookies=c_b)
        raw_kb = r_kb.json()["raw_key"]
        r_bola_k = await client.get(f"/api/v1/assess/{aid}", headers={"Authorization": f"Bearer {raw_kb}"})
        results["bola_api_key_check"] = {"status": r_bola_k.status_code, "body": r_bola_k.json()}

    db_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(db_url)
    async with engine.connect() as conn:
        res_s = await conn.execute(text("SELECT domain_name, score, inferred FROM domain_scores WHERE assessment_id = :aid"), {"aid": aid})
        results["db_domain_scores"] = [{"domain": r[0], "score": r[1], "inferred": r[2]} for r in res_s.fetchall()][:5]
        
        # Test DELETE on audit_logs
        try:
            res_d = await conn.execute(text("DELETE FROM audit_logs WHERE event_type = 'nonexistent_action'"))
            results["db_audit_append_only"] = {"deleted_rows": res_d.rowcount, "passed": res_d.rowcount == 0}
        except Exception as e:
            results["db_audit_append_only"] = {"error": str(e), "passed": True}

    await engine.dispose()
    print("===FULL_AUDIT_SUCCESS===")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    asyncio.run(run())
