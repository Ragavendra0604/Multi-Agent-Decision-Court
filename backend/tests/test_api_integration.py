"""
End-to-End API Integration Tests.
Implements API verification for Modules 1, 2, 4, 5, 8, 36, 37, 39, 40.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.database import init_db
from app.config import settings


@pytest_asyncio.fixture(autouse=True)
async def setup_database(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "mock")
    await init_db()
    yield


@pytest.mark.asyncio
async def test_full_api_workflow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Health check
        health_resp = await client.get("/api/health")
        assert health_resp.status_code == 200
        assert health_resp.json()["status"] == "healthy"

        # 2. Auth profile
        auth_resp = await client.get("/api/auth/me")
        assert auth_resp.status_code == 200
        assert auth_resp.json()["role"] == "ADMIN"

        # 3. Create case via raw text NLP decomposition
        create_payload = {
            "raw_text": "We should adopt Solution X for distributed cache because it offers 40% latency reduction within a $100k budget constraint."
        }
        create_resp = await client.post("/api/cases", json=create_payload)
        assert create_resp.status_code == 201
        case_data = create_resp.json()
        case_id = case_data["case_id"]
        assert case_id.startswith("CASE-")
        assert len(case_data["data"]["claims"]) >= 1

        # 4. Ingest document evidence
        file_content = b"Official Benchmark Report: Solution X demonstrated 40% latency drop under 50k RPS load."
        files = {"file": ("benchmark.txt", file_content, "text/plain")}
        upload_resp = await client.post(f"/api/cases/{case_id}/upload", files=files)
        assert upload_resp.status_code == 200
        assert upload_resp.json()["evidence_items_added"] >= 1

        # 5. Start Court session
        court_resp = await client.post(f"/api/cases/{case_id}/court/start")
        assert court_resp.status_code == 200
        court_data = court_resp.json()
        assert court_data["state"] == "VERDICT_READY"
        assert "verdict" in court_data
        assert "report" in court_data
        assert court_data["findings_count"] >= 5

        # 6. Fetch Verdict
        verdict_resp = await client.get(f"/api/cases/{case_id}/verdict")
        assert verdict_resp.status_code == 200
        assert verdict_resp.json()["verdict"]["case_id"] == case_id

        # 7. Submit Human Review
        review_payload = {
            "reviewer_id": "cdo_reviewer",
            "action": "ACCEPT",
            "notes": "Decision validated by court proceedings and accepted for phased pilot.",
        }
        review_resp = await client.post(f"/api/cases/{case_id}/review", json=review_payload)
        assert review_resp.status_code == 200
        assert review_resp.json()["new_state"] == "CLOSED"

        # 8. Fetch Audit Logs
        audit_resp = await client.get(f"/api/audit/{case_id}")
        assert audit_resp.status_code == 200
        audit_logs = audit_resp.json()
        assert len(audit_logs) >= 3
        event_types = [l["event_type"] for l in audit_logs]
        assert "CASE_CREATED" in event_types
        assert "DOCUMENT_INGESTED" in event_types
        assert "VERDICT_DELIVERED" in event_types
        assert "HUMAN_REVIEW_ACCEPT" in event_types
