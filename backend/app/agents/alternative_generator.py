"""
Alternative Generator Agent & Decision Matrix.
Implements Module 19 (Alternative Generator Agent) & Module 22 (Alternative Comparison Matrix).
Explores credible counter-options and evaluates comparative trade-offs against requirements.
"""

from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from app.schemas.entities import DecisionCase, Alternative, AgentFinding, generate_id
from app.services.llm_provider import BaseLLMProvider, LLMMessage, execute_structured_prompt


class AlternativeOption(BaseModel):
    alt_id: str = Field(default_factory=lambda: generate_id("ALT"))
    title: str
    category: str = Field(description="Do nothing, Optimize current, Partial change, Hybrid, Alternative approach, Defer decision")
    description: str
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)
    estimated_feasibility: float = Field(default=0.7, ge=0.0, le=1.0)
    requirement_fit_score: float = Field(default=0.7, ge=0.0, le=1.0)
    tradeoff_summary: str


class DecisionMatrixRow(BaseModel):
    criterion: str
    proposed_decision_score: float = Field(ge=0.0, le=10.0)
    alternatives_scores: Dict[str, float] = Field(default_factory=dict)
    rationale: str


class AlternativeGenerationOutput(BaseModel):
    proposed_decision_summary: str
    alternatives: List[AlternativeOption] = Field(default_factory=list)
    decision_matrix: List[DecisionMatrixRow] = Field(default_factory=list)
    recommendation_commentary: str


SYSTEM_PROMPT = """You are the Alternative Generator Agent in the Multi-Agent Decision Court.
Your responsibility:
1. Generate realistic, high-quality alternatives to the proposed decision:
   - Do nothing (Status Quo)
   - Optimize current solution / Refactoring
   - Partial / phased change
   - Hybrid approach
   - Alternative tech stack / vendor
   - Defer decision / Proof of Concept
2. Evaluate each alternative against the problem and requirements.
3. Build a Decision Matrix comparing Cost, Performance, Risk, Requirement Fit, and Implementation Feasibility on a 0-10 scale.
"""


class AlternativeGeneratorAgent:
    def __init__(self, provider: BaseLLMProvider):
        self.provider = provider

    async def generate_alternatives(self, case: DecisionCase) -> Tuple[AlternativeGenerationOutput, List[AgentFinding]]:
        reqs_str = "\n".join([f"[{r.req_id}] {r.description}" for r in case.requirements + case.constraints])
        claims_str = "\n".join([f"[{c.claim_id}] {c.statement}" for c in case.claims])

        user_prompt = (
            f"Case: {case.title}\n"
            f"Problem: {case.problem}\n"
            f"Proposed Decision: {case.proposed_decision}\n\n"
            f"REQUIREMENTS & CONSTRAINTS:\n{reqs_str}\n\n"
            f"KEY CLAIMS:\n{claims_str}\n"
        )

        messages = [
            LLMMessage(role="system", content=SYSTEM_PROMPT),
            LLMMessage(role="user", content=user_prompt),
        ]

        result: AlternativeGenerationOutput = await execute_structured_prompt(
            provider=self.provider,
            messages=messages,
            schema=AlternativeGenerationOutput,
        )

        findings = []
        for alt in result.alternatives:
            findings.append(
                AgentFinding(
                    case_id=case.case_id,
                    task_id=generate_id("TASK-AG"),
                    agent="alternative_generator",
                    target_id=alt.alt_id,
                    status="VIABLE_ALTERNATIVE",
                    reason=f"[{alt.category}] {alt.title}: Feasibility {alt.estimated_feasibility:.2f}, Fit {alt.requirement_fit_score:.2f}",
                    confidence=alt.requirement_fit_score,
                    metadata={
                        "category": alt.category,
                        "pros": alt.pros,
                        "cons": alt.cons,
                        "tradeoff": alt.tradeoff_summary,
                    },
                )
            )

        return result, findings
