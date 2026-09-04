"""
Case Analyst Agent.
Implements Module 9 (Case Analyst Agent) & Module 10 (Claim Decomposer Agent).
Analyzes decision objective, scope, ambiguity, and decomposes reasoning into atomic claims.
"""

from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from app.schemas.entities import DecisionCase, Claim, AgentFinding, generate_id
from app.schemas.enums import ClaimSupportStatus
from app.services.llm_provider import BaseLLMProvider, LLMMessage, execute_structured_prompt


class CaseAnalysisOutput(BaseModel):
    objective: str = Field(description="Clear core objective of the decision")
    scope: str = Field(description="Scope boundaries and what is out of scope")
    ambiguities_detected: List[str] = Field(default_factory=list, description="Ambiguous terms or underspecified variables")
    missing_context: List[str] = Field(default_factory=list, description="Missing historical or environmental context")
    atomic_claims: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of atomic claims with statement, category, and is_core_decision_claim"
    )
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)


SYSTEM_PROMPT = """You are the Case Analyst Agent in the Multi-Agent Decision Court.
Your responsibility is to analyze the decision case thoroughly before specialized auditing:
1. Clarify the core decision objective and boundary scope.
2. Detect semantic ambiguities, undefined metrics, or vague terms (e.g. 'faster', 'better', 'soon').
3. Flag critical missing context.
4. Ensure all complex reasoning is decomposed into testable, atomic claims.
"""


class CaseAnalystAgent:
    def __init__(self, provider: BaseLLMProvider):
        self.provider = provider

    async def analyze(self, case: DecisionCase) -> Tuple[CaseAnalysisOutput, List[AgentFinding]]:
        user_prompt = (
            f"Case Title: {case.title}\n"
            f"Problem: {case.problem}\n"
            f"Proposed Decision: {case.proposed_decision}\n"
            f"Context: {case.context or 'None provided'}\n"
            f"Initial Analysis: {case.initial_analysis or 'None provided'}\n"
            f"Existing Claims: {[c.statement for c in case.claims]}\n"
        )
        messages = [
            LLMMessage(role="system", content=SYSTEM_PROMPT),
            LLMMessage(role="user", content=user_prompt),
        ]

        result: CaseAnalysisOutput = await execute_structured_prompt(
            provider=self.provider,
            messages=messages,
            schema=CaseAnalysisOutput,
        )

        findings = [
            AgentFinding(
                case_id=case.case_id,
                task_id=generate_id("TASK-CA"),
                agent="case_analyst",
                target_id=case.case_id,
                status="ANALYZED",
                reason=f"Objective: {result.objective}. Ambiguities flagged: {len(result.ambiguities_detected)}",
                confidence=result.confidence,
                metadata={
                    "scope": result.scope,
                    "ambiguities": result.ambiguities_detected,
                    "missing_context": result.missing_context,
                },
            )
        ]

        return result, findings
