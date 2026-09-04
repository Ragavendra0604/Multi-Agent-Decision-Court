"""
Evidence Investigator Agent.
Implements Module 11 (Evidence Investigator Agent) & Module 6 (Evidence Evaluation).
Validates atomic claims against available evidence, scoring relevance, reliability, and support.
"""

from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from app.schemas.enums import ClaimSupportStatus
from app.schemas.entities import DecisionCase, Claim, Evidence, AgentFinding, generate_id
from app.services.llm_provider import BaseLLMProvider, LLMMessage, execute_structured_prompt


class ClaimInvestigationResult(BaseModel):
    claim_id: str
    status: ClaimSupportStatus = ClaimSupportStatus.UNKNOWN
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    relevance_score: float = Field(default=0.5, ge=0.0, le=1.0)
    reliability_score: float = Field(default=0.5, ge=0.0, le=1.0)
    directness: str = Field(default="DIRECT", description="DIRECT, INDIRECT, CIRCUMSTANTIAL, or NONE")
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    contradicting_evidence_ids: List[str] = Field(default_factory=list)
    findings_summary: str
    missing_evidence_notes: Optional[str] = None


class InvestigationBatchOutput(BaseModel):
    investigations: List[ClaimInvestigationResult] = Field(default_factory=list)


SYSTEM_PROMPT = """You are the Evidence Investigator Agent for the Multi-Agent Decision Court.
Your responsibility is to rigorously audit each claim against available evidence:
1. For every claim, decide if the evidence is SUPPORTED, PARTIALLY_SUPPORTED, UNSUPPORTED, CONTRADICTED, or UNKNOWN.
2. Evaluate evidence reliability, directness, and relevance.
3. Identify contradicting evidence.
4. NEVER fabricate evidence or assume facts that are not provided in the evidence records.
"""


class EvidenceInvestigatorAgent:
    def __init__(self, provider: BaseLLMProvider):
        self.provider = provider

    async def investigate_claims(
        self, case: DecisionCase, evidence_pool: Optional[List[Evidence]] = None
    ) -> Tuple[List[ClaimInvestigationResult], List[AgentFinding]]:
        all_evidence = evidence_pool if evidence_pool is not None else case.evidence

        if not case.claims:
            return [], []

        ev_summary = "\n".join([
            f"[{e.evidence_id}] (Source: {e.source_type.value}, Ref: {e.source_reference or 'N/A'}, Reliability: {e.reliability}): {e.content}"
            for e in all_evidence
        ]) or "No external evidence provided."

        claims_summary = "\n".join([
            f"[{c.claim_id}] Statement: {c.statement} (Category: {c.category or 'General'})"
            for c in case.claims
        ])

        user_prompt = (
            f"Decision Case: {case.title}\n"
            f"Proposed Decision: {case.proposed_decision}\n\n"
            f"CLAIMS TO INVESTIGATE:\n{claims_summary}\n\n"
            f"AVAILABLE EVIDENCE:\n{ev_summary}\n"
        )

        messages = [
            LLMMessage(role="system", content=SYSTEM_PROMPT),
            LLMMessage(role="user", content=user_prompt),
        ]

        result: InvestigationBatchOutput = await execute_structured_prompt(
            provider=self.provider,
            messages=messages,
            schema=InvestigationBatchOutput,
        )

        findings: List[AgentFinding] = []
        for inv in result.investigations:
            findings.append(
                AgentFinding(
                    case_id=case.case_id,
                    task_id=generate_id("TASK-EI"),
                    agent="evidence_investigator",
                    target_id=inv.claim_id,
                    status=inv.status.value,
                    evidence_ids=inv.supporting_evidence_ids + inv.contradicting_evidence_ids,
                    reason=inv.findings_summary,
                    confidence=inv.confidence,
                    requires_followup=inv.status in (ClaimSupportStatus.UNSUPPORTED, ClaimSupportStatus.CONTRADICTED),
                    metadata={
                        "relevance": inv.relevance_score,
                        "reliability": inv.reliability_score,
                        "directness": inv.directness,
                        "missing_notes": inv.missing_evidence_notes,
                    },
                )
            )

        return result.investigations, findings
