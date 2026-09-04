"""
Logic Analyst Agent.
Implements Module 13 (Logic Analyst Agent).
Evaluates deductive and inductive reasoning structures, detects fallacies, and identifies causal vs correlational leaps.
"""

from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from app.schemas.entities import DecisionCase, AgentFinding, generate_id
from app.services.llm_provider import BaseLLMProvider, LLMMessage, execute_structured_prompt


class LogicalFlaw(BaseModel):
    flaw_type: str = Field(description="Type of fallacy or gap (e.g. Unsupported conclusion, False premise, Correlation vs causation, Circular reasoning)")
    description: str
    affected_claims: List[str] = Field(default_factory=list)
    severity: float = Field(default=0.7, ge=0.0, le=1.0)
    remedy_suggestion: Optional[str] = None


class LogicAnalysisOutput(BaseModel):
    overall_logical_validity_score: float = Field(default=0.7, ge=0.0, le=1.0)
    reasoning_structure_soundness: str = Field(default="SOUND", description="SOUND, WEAK, FLAWED, or INVALID")
    flaws_detected: List[LogicalFlaw] = Field(default_factory=list)
    unsupported_leaps: List[str] = Field(default_factory=list)
    summary: str


SYSTEM_PROMPT = """You are the Logic Analyst Agent for the Multi-Agent Decision Court.
Your responsibility:
1. Objectively evaluate the logical structure connecting problem, claims, assumptions, and proposed decision.
2. Check strictly for:
   - Unsupported conclusions & Missing reasoning steps
   - Contradictory or circular reasoning
   - False premises or overgeneralizations
   - Correlation vs causation confusion
   - False analogies or post hoc fallacies
3. Do not make psychological judgments; assess strictly the logical validity of the arguments.
"""


class LogicAnalystAgent:
    def __init__(self, provider: BaseLLMProvider):
        self.provider = provider

    async def analyze_logic(self, case: DecisionCase) -> Tuple[LogicAnalysisOutput, List[AgentFinding]]:
        claims_text = "\n".join([f"[{c.claim_id}] {c.statement}" for c in case.claims])
        assumptions_text = "\n".join([f"[{a.assumption_id}] {a.statement}" for a in case.assumptions])
        
        user_prompt = (
            f"Case: {case.title}\n"
            f"Problem: {case.problem}\n"
            f"Proposed Decision: {case.proposed_decision}\n"
            f"Context / Reasoning: {case.reasoning or case.initial_analysis or 'Direct leap from claims.'}\n\n"
            f"CLAIMS:\n{claims_text}\n\n"
            f"ASSUMPTIONS:\n{assumptions_text}\n"
        )

        messages = [
            LLMMessage(role="system", content=SYSTEM_PROMPT),
            LLMMessage(role="user", content=user_prompt),
        ]

        result: LogicAnalysisOutput = await execute_structured_prompt(
            provider=self.provider,
            messages=messages,
            schema=LogicAnalysisOutput,
        )

        findings = [
            AgentFinding(
                case_id=case.case_id,
                task_id=generate_id("TASK-LA"),
                agent="logic_analyst",
                target_id=case.proposed_decision,
                status=result.reasoning_structure_soundness,
                reason=result.summary,
                confidence=result.overall_logical_validity_score,
                requires_followup=len(result.flaws_detected) > 0,
                metadata={
                    "flaw_count": len(result.flaws_detected),
                    "flaws": [f.model_dump() for f in result.flaws_detected],
                    "unsupported_leaps": result.unsupported_leaps,
                },
            )
        ]

        return result, findings
