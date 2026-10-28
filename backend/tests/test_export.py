"""
Unit and Integration Tests for Decision Dossier Export (Markdown & Printable HTML).
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models.database import init_db
from app.config import settings
from app.schemas.entities import DecisionCase, generate_id
from app.schemas.court import Verdict
from app.services.report_generator import ReportGenerator


@pytest_asyncio.fixture(autouse=True)
async def setup_database(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "mock")
    await init_db()
    yield


@pytest.mark.asyncio
async def test_report_generator_direct_html():
    case = DecisionCase(
        case_id=generate_id("CASE"),
        title="Migrate to Cloud Pub/Sub",
        problem="High broker latency on legacy Kafka cluster",
        proposed_decision="Adopt GCP Cloud Pub/Sub with managed scaling",
    )
    verdict = Verdict(
        case_id=case.case_id,
        summary_verdict_rationale="Approved after validation of latency benchmarks and compliance policies.",
    )

    html = ReportGenerator.generate_html(case, verdict)
    assert "<!DOCTYPE html>" in html
    assert "Migrate to Cloud Pub/Sub" in html
    assert "btn-print" in html
    assert "Executive Decision Court Adjudication Dossier" in html


@pytest.mark.asyncio
async def test_export_endpoints_workflow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create case
        create_payload = {
            "raw_text": "We should adopt System Z to automate risk scoring because it reduces processing time by 80%."
        }
        res = await client.post("/api/cases", json=create_payload)
        assert res.status_code == 201
        case_id = res.json()["case_id"]

        # Before verdict is executed, export should return 404
        md_pre = await client.get(f"/api/cases/{case_id}/export/markdown")
        assert md_pre.status_code == 404

        html_pre = await client.get(f"/api/cases/{case_id}/export/html")
        assert html_pre.status_code == 404

        # Execute court session synchronously
        court_res = await client.post(f"/api/cases/{case_id}/court/start")
        assert court_res.status_code == 200

        # Export Markdown
        md_res = await client.get(f"/api/cases/{case_id}/export/markdown")
        assert md_res.status_code == 200
        assert "text/markdown" in md_res.headers.get("content-type", "")
        assert f"attachment; filename=\"decision-dossier-{case_id}.md\"" in md_res.headers.get("content-disposition", "")
        assert "Multi-Agent Decision Court — Final Verdict Report" in md_res.text
        assert case_id in md_res.text

        # Export HTML
        html_res = await client.get(f"/api/cases/{case_id}/export/html")
        assert html_res.status_code == 200
        assert "text/html" in html_res.headers.get("content-type", "")
        assert "<!DOCTYPE html>" in html_res.text
        assert "window.print()" in html_res.text
        assert case_id in html_res.text

