"""
Theory Analyst Agent.
Implements Module 15 (Theory Analyst Agent).
Evaluates domain theories, theoretical assumptions, preconditions, and applicability bounds.
"""

from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from app.schemas.entities import DecisionCase, Theory, AgentFinding, generate_id
from app.services.llm_provider import BaseLLMProvider, LLMMessage, execute_structured_prompt


class TheoryEvaluationItem(BaseModel):
    theory_id: str
    name: str
    preconditions_satisfied: bool = True
    applicability_score: float = Field(default=0.7, ge=0.0, le=1.0)
    limitations_identified: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    evaluation_summary: str


class TheoryBatchOutput(BaseModel):
    evaluations: List[TheoryEvaluationItem] = Field(default_factory=list)
    summary: str


SYSTEM_PROMPT = """You are the Theory Analyst Agent for the Multi-Agent Decision Court.
Your responsibility:
1. Evaluate user-supplied theoretical models or causal principles (e.g. 'Microservices always improve developer velocity', 'Lower price guarantees market capture').
2. Test whether necessary preconditions are met in this specific context.
3. Identify known theoretical limitations and boundary conditions.
"""


class TheoryAnalystAgent:
    def __init__(self, provider: BaseLLMProvider):
        self.provider = provider

    async def analyze_theories(self, case: DecisionCase) -> Tuple[TheoryBatchOutput, List[AgentFinding]]:
        if not case.theories:
            output = TheoryBatchOutput(
                evaluations=[],
                summary="No theoretical models explicitly invoked in this case.",
            )
            return output, []

        theories_str = "\n".join([
            f"[{t.theory_id}] Name: {t.name}, Preconditions: {t.preconditions}"
            for t in case.theories
        ])

        user_prompt = (
            f"Case: {case.title}\n"
            f"Problem: {case.problem}\n"
            f"Proposed Decision: {case.proposed_decision}\n\n"
            f"THEORIES:\n{theories_str}\n"
        )

        messages = [
            LLMMessage(role="system", content=SYSTEM_PROMPT),
            LLMMessage(role="user", content=user_prompt),
        ]

        result: TheoryBatchOutput = await execute_structured_prompt(
            provider=self.provider,
            messages=messages,
            schema=TheoryBatchOutput,
        )

        findings = []
        for ev in result.evaluations:
            findings.append(
                AgentFinding(
                    case_id=case.case_id,
                    task_id=generate_id("TASK-TA"),
                    agent="theory_analyst",
                    target_id=ev.theory_id,
                    status="APPLICABLE" if ev.preconditions_satisfied else "PRECONDITIONS_UNMET",
                    reason=ev.evaluation_summary,
                    confidence=ev.confidence,
                    metadata={
                        "applicability": ev.applicability_score,
                        "limitations": ev.limitations_identified,
                    },
                )
            )

        return result, findings
