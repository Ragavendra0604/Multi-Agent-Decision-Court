"""
Assumption Auditor Agent.
Implements Module 12 (Assumption Auditor Agent).
Audits explicit assumptions, uncovers hidden assumptions, and maps sensitivity to decision claims.
"""

from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from app.schemas.enums import AssumptionStatus
from app.schemas.entities import DecisionCase, Assumption, AgentFinding, generate_id
from app.services.llm_provider import BaseLLMProvider, LLMMessage, execute_structured_prompt


class AssumptionAuditItem(BaseModel):
    assumption_id: str
    statement: str
    is_explicit: bool = True
    status: AssumptionStatus = AssumptionStatus.UNVERIFIED
    validity_score: float = Field(default=0.5, ge=0.0, le=1.0)
    criticality: float = Field(default=0.5, ge=0.0, le=1.0)
    dependent_claim_ids: List[str] = Field(default_factory=list)
    rationale: str
    risks_if_invalid: Optional[str] = None


class AssumptionAuditBatchOutput(BaseModel):
    audited_assumptions: List[AssumptionAuditItem] = Field(default_factory=list)
    uncovered_hidden_assumptions: List[AssumptionAuditItem] = Field(default_factory=list)


SYSTEM_PROMPT = """You are the Assumption Auditor Agent in the Multi-Agent Decision Court.
Your responsibility:
1. Audit all declared explicit assumptions and assign statuses (VALIDATED, PARTIALLY_VALIDATED, UNVERIFIED, QUESTIONABLE, INVALID).
2. Uncover unstated HIDDEN assumptions necessary for the decision to hold.
3. Map which claims depend on each assumption.
4. Score assumption criticality (how catastrophically the decision fails if this assumption is false).
"""


class AssumptionAuditorAgent:
    def __init__(self, provider: BaseLLMProvider):
        self.provider = provider

    async def audit_assumptions(self, case: DecisionCase) -> Tuple[AssumptionAuditBatchOutput, List[AgentFinding]]:
        existing_assumptions_str = "\n".join([
            f"[{a.assumption_id}] Statement: {a.statement} (Explicit: {a.is_explicit}, Criticality: {a.criticality})"
            for a in case.assumptions
        ]) or "No explicit assumptions declared."

        claims_str = "\n".join([f"[{c.claim_id}] {c.statement}" for c in case.claims])

        user_prompt = (
            f"Decision Case: {case.title}\n"
            f"Problem: {case.problem}\n"
            f"Proposed Decision: {case.proposed_decision}\n\n"
            f"CLAIMS:\n{claims_str}\n\n"
            f"STATED ASSUMPTIONS:\n{existing_assumptions_str}\n"
        )

        messages = [
            LLMMessage(role="system", content=SYSTEM_PROMPT),
            LLMMessage(role="user", content=user_prompt),
        ]

        result: AssumptionAuditBatchOutput = await execute_structured_prompt(
            provider=self.provider,
            messages=messages,
            schema=AssumptionAuditBatchOutput,
        )

        findings: List[AgentFinding] = []
        all_audited = result.audited_assumptions + result.uncovered_hidden_assumptions

        for item in all_audited:
            findings.append(
                AgentFinding(
                    case_id=case.case_id,
                    task_id=generate_id("TASK-AA"),
                    agent="assumption_auditor",
                    target_id=item.assumption_id,
                    status=item.status.value,
                    reason=item.rationale,
                    confidence=item.validity_score,
                    requires_followup=item.status in (AssumptionStatus.QUESTIONABLE, AssumptionStatus.INVALID),
                    metadata={
                        "is_explicit": item.is_explicit,
                        "criticality": item.criticality,
                        "dependent_claims": item.dependent_claim_ids,
                        "risks_if_invalid": item.risks_if_invalid,
                    },
                )
            )

        return result, findings
