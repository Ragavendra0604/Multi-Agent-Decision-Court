"""
Memory Layer.
Implements Module 31 (Memory: Case Memory, Session Memory, and Knowledge Memory)
with tenant/case isolation.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.schemas.entities import (
    DecisionCase,
    AgentFinding,
)
from app.schemas.court import (
    Verdict,
    Argument,
    CrossExaminationTurn,
)


class SessionTurn(BaseModel):
    turn_id: str
    role: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CaseMemory(BaseModel):
    case_id: str
    tenant_id: str = "default_tenant"
    findings: List[AgentFinding] = Field(default_factory=list)
    arguments: List[Argument] = Field(default_factory=list)
    cross_examinations: List[CrossExaminationTurn] = Field(default_factory=list)
    latest_verdict: Optional[Verdict] = None
    historical_verdicts: List[Verdict] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SessionMemory(BaseModel):
    session_id: str
    case_id: str
    turns: List[SessionTurn] = Field(default_factory=list)
    user_overrides: List[Dict[str, Any]] = Field(default_factory=list)


class KnowledgeDocument(BaseModel):
    doc_id: str
    title: str
    category: str
    content: str
    tags: List[str] = Field(default_factory=list)
    tenant_id: str = "default_tenant"


class MemoryManager:
    """
    Unified manager for Case, Session, and Knowledge Memory stores.
    """
    def __init__(self):
        self._case_stores: Dict[str, CaseMemory] = {}
        self._session_stores: Dict[str, SessionMemory] = {}
        self._knowledge_stores: Dict[str, List[KnowledgeDocument]] = {}

    def get_or_create_case_memory(self, case_id: str, tenant_id: str = "default_tenant") -> CaseMemory:
        key = f"{tenant_id}:{case_id}"
        if key not in self._case_stores:
            self._case_stores[key] = CaseMemory(case_id=case_id, tenant_id=tenant_id)
        return self._case_stores[key]

    def add_agent_finding(self, case_id: str, finding: AgentFinding, tenant_id: str = "default_tenant") -> None:
        mem = self.get_or_create_case_memory(case_id, tenant_id)
        mem.findings.append(finding)

    def add_argument(self, case_id: str, argument: Argument, tenant_id: str = "default_tenant") -> None:
        mem = self.get_or_create_case_memory(case_id, tenant_id)
        mem.arguments.append(argument)

    def add_cross_examination(self, case_id: str, turn: CrossExaminationTurn, tenant_id: str = "default_tenant") -> None:
        mem = self.get_or_create_case_memory(case_id, tenant_id)
        mem.cross_examinations.append(turn)

    def record_verdict(self, case_id: str, verdict: Verdict, tenant_id: str = "default_tenant") -> None:
        mem = self.get_or_create_case_memory(case_id, tenant_id)
        if mem.latest_verdict:
            mem.historical_verdicts.append(mem.latest_verdict)
        mem.latest_verdict = verdict

    def add_session_turn(self, session_id: str, case_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        if session_id not in self._session_stores:
            self._session_stores[session_id] = SessionMemory(session_id=session_id, case_id=case_id)
        turn = SessionTurn(
            turn_id=f"turn-{len(self._session_stores[session_id].turns) + 1}",
            role=role,
            content=content,
            metadata=metadata or {},
        )
        self._session_stores[session_id].turns.append(turn)

    def get_session_history(self, session_id: str) -> List[SessionTurn]:
        if session_id in self._session_stores:
            return self._session_stores[session_id].turns
        return []

    def add_knowledge_doc(self, doc: KnowledgeDocument) -> None:
        tenant = doc.tenant_id
        if tenant not in self._knowledge_stores:
            self._knowledge_stores[tenant] = []
        self._knowledge_stores[tenant].append(doc)

    def search_knowledge(self, query: str, tenant_id: str = "default_tenant", limit: int = 5) -> List[KnowledgeDocument]:
        docs = self._knowledge_stores.get(tenant_id, [])
        query_words = set(query.lower().split())
        scored_docs = []
        for d in docs:
            score = 0
            doc_text = (d.title + " " + d.content + " " + " ".join(d.tags)).lower()
            for w in query_words:
                if w in doc_text:
                    score += 1
            if score > 0:
                scored_docs.append((score, d))
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        return [d for _, d in scored_docs[:limit]]


memory_manager = MemoryManager()
