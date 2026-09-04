"""
Evidence Reconciliation Engine.
Implements Module 21 (Evidence Reconciliation).
Compares conflicting evidence, analyzes source authority, date recency, applicability,
and preserves unresolved conflicts for judicial review.
"""

from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from app.schemas.enums import ReconciliationStatus
from app.schemas.entities import DecisionCase, Evidence, AgentFinding, generate_id
from app.schemas.court import ReconciledEvidenceItem
from app.services.llm_provider import BaseLLMProvider, LLMMessage, execute_structured_prompt


class ReconciliationItemOutput(BaseModel):
    topic_or_claim_id: str
    conflicting_evidence_ids: List[str] = Field(default_factory=list)
    status: ReconciliationStatus = ReconciliationStatus.PARTIALLY_RESOLVED
    resolution_rationale: str
    authority_comparison: str = Field(description="Comparison of source credibility/authority")
    date_comparison: str = Field(description="Comparison of timestamp and recency")
    applicability_comparison: str = Field(description="Comparison of contextual applicability")


class ReconciliationBatchOutput(BaseModel):
    reconciled_items: List[ReconciliationItemOutput] = Field(default_factory=list)
    summary: str


SYSTEM_PROMPT = """You are the Evidence Reconciliation Agent in the Multi-Agent Decision Court.
Your responsibility:
1. Reconcile disagreements between conflicting evidence items or contradictory agent findings.
2. Formally evaluate:
   - Source Authority & Provenance (e.g. Peer-reviewed vendor audit vs casual blog post)
   - Date Recency (newer metrics supersede legacy benchmarks)
   - Contextual Applicability (e.g. synthetic test vs real-world production workload)
3. Assign resolution status: RESOLVED_FOR, RESOLVED_AGAINST, PARTIALLY_RESOLVED, or UNRESOLVED.
4. RULE: Never force a false consensus. If true empirical uncertainty persists, mark it UNRESOLVED.
"""


class EvidenceReconciliationEngine:
    def __init__(self, provider: BaseLLMProvider):
        self.provider = provider

    async def reconcile_conflicts(
        self, case: DecisionCase, conflicting_evidence: List[Evidence]
    ) -> Tuple[List[ReconciledEvidenceItem], List[AgentFinding]]:
        if len(conflicting_evidence) < 2:
            return [], []

        ev_str = "\n".join([
            f"[{e.evidence_id}] Source: {e.source_type.value}, Ref: {e.source_reference or 'N/A'}, Date: {e.timestamp.isoformat()}, Reliability: {e.reliability}\nContent: {e.content}"
            for e in conflicting_evidence
        ])

        user_prompt = (
            f"Case Decision: {case.proposed_decision}\n\n"
            f"CONFLICTING EVIDENCE RECORDS TO RECONCILE:\n{ev_str}\n"
        )

        messages = [
            LLMMessage(role="system", content=SYSTEM_PROMPT),
            LLMMessage(role="user", content=user_prompt),
        ]

        result: ReconciliationBatchOutput = await execute_structured_prompt(
            provider=self.provider,
            messages=messages,
            schema=ReconciliationBatchOutput,
        )

        reconciled_items = []
        findings = []

        for rec in result.reconciled_items:
            item = ReconciledEvidenceItem(
                reconciliation_id=generate_id("REC"),
                topic_or_claim_id=rec.topic_or_claim_id,
                conflicting_evidence_ids=rec.conflicting_evidence_ids,
                status=rec.status,
                resolution_rationale=rec.resolution_rationale,
                authority_comparison=rec.authority_comparison,
                date_comparison=rec.date_comparison,
                applicability_comparison=rec.applicability_comparison,
            )
            reconciled_items.append(item)

            findings.append(
                AgentFinding(
                    case_id=case.case_id,
                    task_id=generate_id("TASK-REC"),
                    agent="reconciliation",
                    target_id=rec.topic_or_claim_id,
                    status=rec.status.value,
                    evidence_ids=rec.conflicting_evidence_ids,
                    reason=rec.resolution_rationale,
                    confidence=0.85,
                    requires_followup=rec.status == ReconciliationStatus.UNRESOLVED,
                    metadata={
                        "authority": rec.authority_comparison,
                        "date": rec.date_comparison,
                        "applicability": rec.applicability_comparison,
                    },
                )
            )

        return reconciled_items, findings
