"""
Risk Analyst Agent.
Implements Module 18 (Risk Analyst Agent).
Identifies operational, technical, financial, compliance, security, and execution risks,
avoiding false precision and linking risks to affected claims.
"""

from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from app.schemas.enums import RiskCategory
from app.schemas.entities import DecisionCase, Risk, AgentFinding, generate_id
from app.services.llm_provider import BaseLLMProvider, LLMMessage, execute_structured_prompt


class RiskAssessmentItem(BaseModel):
    risk_id: str
    category: RiskCategory = RiskCategory.UNKNOWN
    description: str
    probability: float = Field(default=0.5, ge=0.0, le=1.0)
    impact: float = Field(default=0.5, ge=0.0, le=1.0)
    severity_score: float = Field(default=0.25, ge=0.0, le=1.0)
    mitigation_suggested: Optional[str] = None
    affected_claim_ids: List[str] = Field(default_factory=list)


class RiskAnalysisOutput(BaseModel):
    overall_risk_level: str = Field(default="MODERATE", description="LOW, MODERATE, HIGH, or CRITICAL")
    max_severity: float = Field(default=0.5, ge=0.0, le=1.0)
    identified_risks: List[RiskAssessmentItem] = Field(default_factory=list)
    executive_risk_summary: str


SYSTEM_PROMPT = """You are the Risk Analyst Agent in the Multi-Agent Decision Court.
Your responsibility:
1. Dynamically uncover potential failure modes across Technical, Financial, Operational, Security, Compliance, Scalability, and Execution categories.
2. Estimate realistic probability and impact scores (severity = probability * impact).
3. Explicitly link risks to claims they threaten.
4. Suggest concrete mitigation actions.
"""


class RiskAnalystAgent:
    def __init__(self, provider: BaseLLMProvider):
        self.provider = provider

    async def analyze_risks(self, case: DecisionCase) -> Tuple[RiskAnalysisOutput, List[AgentFinding]]:
        existing_risks = "\n".join([
            f"[{r.risk_id}] ({r.category.value}): {r.description} (Severity: {r.severity_score})"
            for r in case.risks
        ]) or "No pre-identified risks declared."

        claims_str = "\n".join([f"[{c.claim_id}] {c.statement}" for c in case.claims])
        assumptions_str = "\n".join([f"[{a.assumption_id}] {a.statement}" for a in case.assumptions])

        user_prompt = (
            f"Case Title: {case.title}\n"
            f"Problem: {case.problem}\n"
            f"Proposed Decision: {case.proposed_decision}\n\n"
            f"CLAIMS:\n{claims_str}\n\n"
            f"ASSUMPTIONS:\n{assumptions_str}\n\n"
            f"KNOWN RISKS:\n{existing_risks}\n"
        )

        messages = [
            LLMMessage(role="system", content=SYSTEM_PROMPT),
            LLMMessage(role="user", content=user_prompt),
        ]

        result: RiskAnalysisOutput = await execute_structured_prompt(
            provider=self.provider,
            messages=messages,
            schema=RiskAnalysisOutput,
        )

        findings = []
        for rk in result.identified_risks:
            findings.append(
                AgentFinding(
                    case_id=case.case_id,
                    task_id=generate_id("TASK-RA"),
                    agent="risk_analyst",
                    target_id=rk.risk_id,
                    status=f"SEVERITY_{rk.severity_score:.2f}",
                    reason=f"[{rk.category.value}] {rk.description}",
                    confidence=rk.severity_score,
                    requires_followup=rk.severity_score >= 0.5,
                    metadata={
                        "category": rk.category.value,
                        "probability": rk.probability,
                        "impact": rk.impact,
                        "mitigation": rk.mitigation_suggested,
                        "affected_claims": rk.affected_claim_ids,
                    },
                )
            )

        return result, findings
