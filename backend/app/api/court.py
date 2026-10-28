"""
Court Proceedings, Verdict, Human-in-the-Loop & WebSocket Endpoints.
Implements Module 40 (API Design), Module 42 (Live Court UI Streaming),
and Module 36 (Human-in-the-Loop Review).
"""

import asyncio
import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db, async_session
from app.models.db_models import CaseDB, VerdictDB, HumanReviewDB, AuditLogDB
from app.schemas.entities import DecisionCase, AgentFinding, generate_id
from app.schemas.enums import CaseState, HumanReviewAction
from app.schemas.court import Verdict, FinalDecisionReport
from app.orchestration.court_orchestrator import CourtOrchestrator, CourtEvent, CourtExecutionResult
from app.memory.memory_manager import memory_manager
from app.services.llm_provider import get_llm_provider
from app.services.report_generator import ReportGenerator
from app.agents.sensitivity_engine import SensitivityEngine

router = APIRouter(prefix="/api/cases", tags=["Court"])

# Active WebSocket connections per case
_connections: Dict[str, List[WebSocket]] = {}


class HumanReviewRequest(BaseModel):
    reviewer_id: str = "human_evaluator"
    action: HumanReviewAction = HumanReviewAction.ACCEPT
    notes: str
    override_reason: Optional[str] = None


class WhatIfRequest(BaseModel):
    condition: str
    variable_changed: Optional[str] = None


async def broadcast_event(case_id: str, event: CourtEvent):
    if case_id in _connections:
        dead_sockets = []
        payload = event.model_dump(mode="json")
        for ws in _connections[case_id]:
            try:
                await ws.send_json(payload)
            except Exception:
                dead_sockets.append(ws)
        for ws in dead_sockets:
            if ws in _connections[case_id]:
                _connections[case_id].remove(ws)


@router.websocket("/{case_id}/ws")
async def court_websocket(websocket: WebSocket, case_id: str):
    await websocket.accept()
    if case_id not in _connections:
        _connections[case_id] = []
    _connections[case_id].append(websocket)
    try:
        while True:
            # Keep socket alive and receive any client messages
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        if case_id in _connections and websocket in _connections[case_id]:
            _connections[case_id].remove(websocket)


async def _execute_court_session_job(case_id: str):
    """
    Background worker that runs the full multi-agent court proceedings,
    broadcasts live WebSocket events, and persists the verdict upon completion.
    """
    async with async_session() as db:
        res = await db.execute(select(CaseDB).where(CaseDB.case_id == case_id))
        c = res.scalar_one_or_none()
        if not c:
            return

        data = json.loads(c.data_json or "{}")
        decision_case = DecisionCase.model_validate(data)

        def on_event(evt: CourtEvent):
            asyncio.create_task(broadcast_event(case_id, evt))

        provider = get_llm_provider()
        orchestrator = CourtOrchestrator(provider=provider, event_callback=on_event)

        try:
            court_result: CourtExecutionResult = await orchestrator.execute_court_session(decision_case)
            c.state = CaseState.VERDICT_READY.value
            verdict_db = VerdictDB(
                verdict_id=court_result.verdict.verdict_id,
                case_id=case_id,
                version=c.version,
                verdict=court_result.verdict.verdict.value,
                confidence=court_result.verdict.confidence,
                correctness_status=court_result.verdict.decision_correctness.status.value,
                justification_status=court_result.verdict.decision_justification.status.value,
                summary_rationale=court_result.verdict.summary_verdict_rationale,
                verdict_json=json.dumps(court_result.verdict.model_dump(mode="json")),
            )
            db.add(verdict_db)

            audit = AuditLogDB(
                case_id=case_id,
                event_type="VERDICT_DELIVERED",
                actor="judge_agent",
                details=json.dumps({
                    "verdict": court_result.verdict.verdict.value,
                    "confidence": court_result.verdict.confidence,
                    "duration": court_result.duration_seconds,
                }),
            )
            db.add(audit)
            await db.commit()

            # Final broadcast for connected clients
            await broadcast_event(case_id, CourtEvent(
                case_id=case_id,
                phase="VERDICT_READY",
                message=f"Verdict delivered: {court_result.verdict.verdict.value} (Confidence: {court_result.verdict.confidence:.2f})",
                agent="judge",
                payload={"verdict": court_result.verdict.model_dump(mode="json")}
            ))
            return court_result
        except Exception as e:
            c.state = CaseState.DRAFT.value
            await db.commit()
            await broadcast_event(case_id, CourtEvent(
                case_id=case_id,
                phase="ERROR",
                message=f"Court proceedings interrupted: {str(e)}",
                agent="court",
            ))
            raise e


@router.post("/{case_id}/court/start")
async def start_court_session(
    case_id: str, 
    background: bool = False,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(CaseDB).where(CaseDB.case_id == case_id))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found.")

    c.state = CaseState.ANALYZING.value
    await db.commit()

    if background:
        # Launch background task to avoid HTTP timeout
        asyncio.create_task(_execute_court_session_job(case_id))
        return {
            "status": "started",
            "case_id": case_id,
            "state": "ANALYZING",
            "message": "Court session running asynchronously. Streaming events via WebSocket."
        }
    else:
        # Synchronous execution mode (for direct API tests)
        court_result = await _execute_court_session_job(case_id)
        return {
            "case_id": case_id,
            "state": "VERDICT_READY",
            "verdict": court_result.verdict.model_dump(mode="json") if court_result else None,
            "report": court_result.report.model_dump(mode="json") if court_result else None,
            "graph": court_result.graph_data if court_result else None,
            "findings_count": len(court_result.findings) if court_result else 0,
            "duration_seconds": court_result.duration_seconds if court_result else 0,
        }


@router.get("/{case_id}/findings")
async def get_findings(case_id: str):
    mem = memory_manager.get_or_create_case_memory(case_id)
    return {
        "case_id": case_id,
        "findings": [f.model_dump(mode="json") for f in mem.findings],
        "arguments": [a.model_dump(mode="json") for a in mem.arguments],
        "cross_examinations": [t.model_dump(mode="json") for t in mem.cross_examinations],
    }


@router.get("/{case_id}/verdict")
async def get_verdict(case_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(VerdictDB).where(VerdictDB.case_id == case_id).order_by(VerdictDB.created_at.desc())
    )
    v = result.scalar_one_or_none()
    if not v:
        raise HTTPException(status_code=404, detail="No verdict available yet for this case.")

    verdict_dict = json.loads(v.verdict_json)
    return {
        "verdict_id": v.verdict_id,
        "case_id": v.case_id,
        "verdict": verdict_dict,
    }


@router.post("/{case_id}/review")
async def submit_human_review(case_id: str, req: HumanReviewRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CaseDB).where(CaseDB.case_id == case_id))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found.")

    review_db = HumanReviewDB(
        review_id=generate_id("REV"),
        case_id=case_id,
        reviewer_id=req.reviewer_id,
        action=req.action.value,
        notes=req.notes,
        override_reason=req.override_reason,
    )
    db.add(review_db)

    c.state = CaseState.CLOSED.value if req.action == HumanReviewAction.ACCEPT else CaseState.HUMAN_REVIEW.value

    audit = AuditLogDB(
        case_id=case_id,
        event_type=f"HUMAN_REVIEW_{req.action.value}",
        actor=req.reviewer_id,
        details=json.dumps({"notes": req.notes, "override": req.override_reason}),
    )
    db.add(audit)
    await db.commit()

    return {
        "message": f"Human review submitted: {req.action.value}",
        "case_id": case_id,
        "new_state": c.state,
    }


@router.post("/{case_id}/what-if")
async def run_what_if_scenario(case_id: str, req: WhatIfRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CaseDB).where(CaseDB.case_id == case_id))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found.")

    mem = memory_manager.get_or_create_case_memory(case_id)
    if not mem.latest_verdict:
        raise HTTPException(status_code=400, detail="Must execute court session before running What-If scenarios.")

    data = json.loads(c.data_json or "{}")
    decision_case = DecisionCase.model_validate(data)

    provider = get_llm_provider()
    engine = SensitivityEngine(provider)
    sensitivity_out, _ = await engine.run_sensitivity_analysis(decision_case, mem.latest_verdict)

    return {
        "case_id": case_id,
        "condition_tested": req.condition,
        "sensitivity_analysis": sensitivity_out.model_dump(mode="json"),
    }

@router.get("/{case_id}/export/markdown")
async def export_verdict_markdown(case_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CaseDB).where(CaseDB.case_id == case_id))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found.")

    v_res = await db.execute(select(VerdictDB).where(VerdictDB.case_id == case_id))
    v = v_res.scalar_one_or_none()
    if not v:
        raise HTTPException(status_code=404, detail="No verdict available yet for this case.")

    decision_case = DecisionCase.model_validate(json.loads(c.data_json or "{}"))
    verdict = Verdict.model_validate(json.loads(v.verdict_json))

    mem = memory_manager.get_or_create_case_memory(case_id)
    report = ReportGenerator.generate_report(
        case=decision_case,
        verdict=verdict,
        cross_examinations=getattr(mem, "cross_examinations", None),
        reconciliations=getattr(mem, "reconciled_evidence", None),
    )

    filename = f"decision-dossier-{case_id}.md"
    return Response(
        content=report.markdown_content,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{case_id}/export/html")
async def export_verdict_html(case_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CaseDB).where(CaseDB.case_id == case_id))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found.")

    v_res = await db.execute(select(VerdictDB).where(VerdictDB.case_id == case_id))
    v = v_res.scalar_one_or_none()
    if not v:
        raise HTTPException(status_code=404, detail="No verdict available yet for this case.")

    decision_case = DecisionCase.model_validate(json.loads(c.data_json or "{}"))
    verdict = Verdict.model_validate(json.loads(v.verdict_json))

    mem = memory_manager.get_or_create_case_memory(case_id)
    html_content = ReportGenerator.generate_html(
        case=decision_case,
        verdict=verdict,
        cross_examinations=getattr(mem, "cross_examinations", None),
        reconciliations=getattr(mem, "reconciled_evidence", None),
    )

    return HTMLResponse(content=html_content)

