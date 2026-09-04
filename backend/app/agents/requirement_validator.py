"""
Requirement Validator Agent.
Implements Module 14 (Requirement Validator Agent).
Maps the proposed decision and supporting claims against all functional requirements and non-negotiable constraints.
"""

from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from app.schemas.enums import RequirementStatus
from app.schemas.entities import DecisionCase, Requirement, AgentFinding, generate_id
from app.services.llm_provider import BaseLLMProvider, LLMMessage, execute_structured_prompt


class RequirementAuditItem(BaseModel):
    req_id: str
    description: str
    is_critical_constraint: bool = False
    status: RequirementStatus = RequirementStatus.UNKNOWN
    satisfaction_score: float = Field(default=0.5, ge=0.0, le=1.0)
    supporting_factors: List[str] = Field(default_factory=list)
    violating_factors: List[str] = Field(default_factory=list)
    justification: str


class RequirementValidationBatchOutput(BaseModel):
    overall_satisfaction_score: float = Field(default=0.7, ge=0.0, le=1.0)
    has_critical_violation: bool = False
    evaluations: List[RequirementAuditItem] = Field(default_factory=list)
    summary: str


SYSTEM_PROMPT = """You are the Requirement Validator Agent for the Multi-Agent Decision Court.
Your responsibility:
1. Map the proposed decision and claim evidence against every requirement and constraint.
2. Determine if each requirement is SATISFIED, PARTIALLY_SATISFIED, UNSATISFIED, or UNKNOWN.
3. Check specifically for critical constraint violations.
4. Rule: A decision cannot be considered validated if it violates any critical requirement or constraint.
"""


class RequirementValidatorAgent:
    def __init__(self, provider: BaseLLMProvider):
        self.provider = provider

    async def validate_requirements(self, case: DecisionCase) -> Tuple[RequirementValidationBatchOutput, List[AgentFinding]]:
        reqs = case.requirements + case.constraints
        if not reqs:
            # Generate default passing evaluation
            output = RequirementValidationBatchOutput(
                overall_satisfaction_score=0.8,
                has_critical_violation=False,
                evaluations=[],
                summary="No explicit requirements or constraints defined.",
            )
            return output, []

        reqs_str = "\n".join([
            f"[{r.req_id}] {'[CRITICAL CONSTRAINT]' if r.is_constraint or r.is_critical else '[REQUIREMENT]'}: {r.description}"
            for r in reqs
        ])
        claims_str = "\n".join([f"[{c.claim_id}] {c.statement}" for c in case.claims])

        user_prompt = (
            f"Case: {case.title}\n"
            f"Proposed Decision: {case.proposed_decision}\n\n"
            f"REQUIREMENTS & CONSTRAINTS:\n{reqs_str}\n\n"
            f"CLAIMS & EVIDENCE CONTEXT:\n{claims_str}\n"
        )

        messages = [
            LLMMessage(role="system", content=SYSTEM_PROMPT),
            LLMMessage(role="user", content=user_prompt),
        ]

        result: RequirementValidationBatchOutput = await execute_structured_prompt(
            provider=self.provider,
            messages=messages,
            schema=RequirementValidationBatchOutput,
        )

        findings: List[AgentFinding] = []
        for audit in result.evaluations:
            findings.append(
                AgentFinding(
                    case_id=case.case_id,
                    task_id=generate_id("TASK-RV"),
                    agent="requirement_validator",
                    target_id=audit.req_id,
                    status=audit.status.value,
                    reason=audit.justification,
                    confidence=audit.satisfaction_score,
                    requires_followup=audit.status == RequirementStatus.UNSATISFIED and audit.is_critical_constraint,
                    metadata={
                        "is_critical": audit.is_critical_constraint,
                        "supporting_factors": audit.supporting_factors,
                        "violating_factors": audit.violating_factors,
                    },
                )
            )

        return result, findings
