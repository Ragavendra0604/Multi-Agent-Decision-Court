"""
Case Management REST Endpoints.
Implements Module 2 (Case Management), Module 4 (NLP Decomposer API),
Module 5 (Document Upload Ingestion), and Module 35 (Versioning).
"""

import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.db_models import CaseDB, CaseVersionDB, AuditLogDB
from app.schemas.entities import DecisionCase, Evidence, generate_id
from app.schemas.enums import CaseState, ProvenanceType
from app.decision_graph.graph_engine import DecisionGraph
from app.agents.decomposer import CaseDecomposer
from app.evidence.doc_ingestion import DocumentParser
from app.services.llm_provider import get_llm_provider

router = APIRouter(prefix="/api/cases", tags=["Cases"])


class CreateCaseRequest(BaseModel):
    title: Optional[str] = None
    problem: Optional[str] = None
    proposed_decision: Optional[str] = None
    raw_text: Optional[str] = None
    context: Optional[str] = None
    requirements: List[str] = []
    constraints: List[str] = []


class CaseResponse(BaseModel):
    case_id: str
    title: str
    problem: str
    proposed_decision: str
    state: str
    version: int
    data: Dict[str, Any]
    graph: Dict[str, Any]


@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(req: CreateCaseRequest, db: AsyncSession = Depends(get_db)):
    provider = get_llm_provider()
    target_case_id = generate_id("CASE")

    # If raw free-form text is provided, decompose using Module 4 Decomposer
    if req.raw_text and (not req.problem or not req.proposed_decision):
        decomposer = CaseDecomposer(provider)
        decision_case = await decomposer.decompose_text(req.raw_text, case_id=target_case_id)
        if req.title:
            decision_case.title = req.title
    else:
        if not req.problem or not req.proposed_decision:
            raise HTTPException(status_code=400, detail="Either 'raw_text' or both 'problem' and 'proposed_decision' must be provided.")
        
        decision_case = DecisionCase(
            case_id=target_case_id,
            title=req.title or "Untitled Decision Case",
            problem=req.problem,
            proposed_decision=req.proposed_decision,
            context=req.context,
        )

    graph = DecisionGraph.from_case(decision_case)
    case_dict = decision_case.model_dump(mode="json")

    case_db = CaseDB(
        case_id=target_case_id,
        title=decision_case.title,
        problem=decision_case.problem,
        proposed_decision=decision_case.proposed_decision,
        context=decision_case.context,
        state=CaseState.DRAFT.value,
        version=1,
        data_json=json.dumps(case_dict),
    )
    db.add(case_db)

    # Add initial version snapshot (Module 35)
    version_db = CaseVersionDB(
        case_id=target_case_id,
        version=1,
        snapshot_json=json.dumps(case_dict),
        change_summary="Initial case creation",
    )
    db.add(version_db)

    # Add audit log (Module 37)
    audit = AuditLogDB(
        case_id=target_case_id,
        event_type="CASE_CREATED",
        actor="user",
        details=json.dumps({"title": decision_case.title}),
    )
    db.add(audit)

    await db.commit()

    return CaseResponse(
        case_id=target_case_id,
        title=decision_case.title,
        problem=decision_case.problem,
        proposed_decision=decision_case.proposed_decision,
        state=CaseState.DRAFT.value,
        version=1,
        data=case_dict,
        graph=graph.to_data().model_dump(),
    )


@router.get("", response_model=List[CaseResponse])
async def list_cases(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CaseDB).order_by(CaseDB.created_at.desc()))
    cases = result.scalars().all()

    response = []
    for c in cases:
        data = json.loads(c.data_json or "{}")
        d_case = DecisionCase.model_validate(data) if data else DecisionCase(case_id=c.case_id, title=c.title, problem=c.problem, proposed_decision=c.proposed_decision)
        graph = DecisionGraph.from_case(d_case)
        response.append(
            CaseResponse(
                case_id=c.case_id,
                title=c.title,
                problem=c.problem,
                proposed_decision=c.proposed_decision,
                state=c.state,
                version=c.version,
                data=data,
                graph=graph.to_data().model_dump(),
            )
        )
    return response


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(case_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CaseDB).where(CaseDB.case_id == case_id))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found.")

    data = json.loads(c.data_json or "{}")
    d_case = DecisionCase.model_validate(data) if data else DecisionCase(case_id=c.case_id, title=c.title, problem=c.problem, proposed_decision=c.proposed_decision)
    graph = DecisionGraph.from_case(d_case)

    return CaseResponse(
        case_id=c.case_id,
        title=c.title,
        problem=c.problem,
        proposed_decision=c.proposed_decision,
        state=c.state,
        version=c.version,
        data=data,
        graph=graph.to_data().model_dump(),
    )


@router.post("/{case_id}/upload")
async def upload_document(
    case_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Ingests PDF, DOCX, TXT, or JSON file, chunks it, and appends extracted evidence to case.
    """
    result = await db.execute(select(CaseDB).where(CaseDB.case_id == case_id))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found.")

    content_bytes = await file.read()
    chunks = DocumentParser.parse_file(content_bytes, file.filename or "uploaded_doc")

    data = json.loads(c.data_json or "{}")
    d_case = DecisionCase.model_validate(data)

    new_evidence_items = [chunk.to_evidence() for chunk in chunks]
    d_case.evidence.extend(new_evidence_items)

    c.data_json = json.dumps(d_case.model_dump(mode="json"))
    
    # Audit log
    audit = AuditLogDB(
        case_id=case_id,
        event_type="DOCUMENT_INGESTED",
        actor="user",
        details=json.dumps({"filename": file.filename, "chunks_count": len(chunks)}),
    )
    db.add(audit)
    await db.commit()

    return {
        "message": f"Successfully ingested {file.filename}",
        "chunks_extracted": len(chunks),
        "evidence_items_added": len(new_evidence_items),
    }
