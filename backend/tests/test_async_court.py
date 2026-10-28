import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_async_court_background_execution():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create case
        resp = await client.post("/api/cases", json={
            "title": "Background Job Test Case",
            "problem": "Performance bottleneck under high concurrency",
            "proposed_decision": "Implement Redis read-replica cache cluster"
        })
        assert resp.status_code == 201
        case_id = resp.json()["case_id"]

        # Call with background=true
        start_resp = await client.post(f"/api/cases/{case_id}/court/start?background=true")
        assert start_resp.status_code == 200
        data = start_resp.json()
        assert data["status"] == "started"
        assert data["state"] == "ANALYZING"

