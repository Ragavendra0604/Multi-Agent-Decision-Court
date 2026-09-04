"""
Sensitivity & What-If Analysis Engine.
Implements Module 23 (Sensitivity & What-If Engine).
Simulates variations in assumptions, costs, evidence presence, and requirement priorities to discover
decision tipping points and vulnerabilities.
"""

from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from app.schemas.entities import DecisionCase, Assumption, Evidence, AgentFinding, generate_id
from app.schemas.court import Verdict
from app.services.llm_provider import BaseLLMProvider, LLMMessage, execute_structured_prompt


class WhatIfScenarioResult(BaseModel):
    scenario_id: str = Field(default_factory=lambda: generate_id("SCENARIO"))
    scenario_title: str
    condition_tested: str = Field(description="e.g., 'What if assumption A-01 is invalidated?', 'What if migration cost doubles?'")
    verdict_impact: str = Field(description="UNCHANGED, DOWNGRADED_TO_PARTIALLY_VALID, FLIPPED_TO_INVALID, or HIGH_RISK")
    tipping_point_threshold: Optional[str] = None
    recommended_pivot: Optional[str] = None
    rationale: str


class SensitivityAnalysisOutput(BaseModel):
    most_fragile_assumptions: List[str] = Field(default_factory=list)
    critical_cost_or_risk_thresholds: List[str] = Field(default_factory=list)
    scenarios: List[WhatIfScenarioResult] = Field(default_factory=list)
    robustness_score: float = Field(default=0.7, ge=0.0, le=1.0, description="Overall decision robustness to variable fluctuations")


SYSTEM_PROMPT = """You are the Sensitivity & What-If Analyst in the Multi-Agent Decision Court.
Your responsibility:
1. Conduct stress-testing and sensitivity analysis on the decision verdict.
2. Formulate realistic What-If scenarios:
   - What if a critical assumption fails?
   - What if costs or timeline exceed estimates by 50% or 100%?
   - What if a core piece of evidence is removed or discredited?
   - What if requirement priorities shift?
3. Pinpoint exact tipping points where the decision flips from viable to invalid, and identify recommended pivot alternatives.
"""


class SensitivityEngine:
    def __init__(self, provider: BaseLLMProvider):
        self.provider = provider

    async def run_sensitivity_analysis(
        self, case: DecisionCase, verdict: Verdict
    ) -> Tuple[SensitivityAnalysisOutput, List[AgentFinding]]:
        assumptions_str = "\n".join([f"[{a.assumption_id}] {a.statement} (Criticality: {a.criticality})" for a in case.assumptions])
        claims_str = "\n".join([f"[{c.claim_id}] {c.statement}" for c in case.claims])
        alts_str = "\n".join([f"[{alt.alt_id}] {alt.title}" for alt in case.alternatives])

        user_prompt = (
            f"Case: {case.title}\n"
            f"Proposed Decision: {case.proposed_decision}\n"
            f"Current Verdict: {verdict.verdict.value} (Confidence: {verdict.confidence:.2f})\n"
            f"Decision Drivers: {verdict.critical_decision_drivers}\n\n"
            f"ASSUMPTIONS:\n{assumptions_str}\n\n"
            f"CLAIMS:\n{claims_str}\n\n"
            f"ALTERNATIVES:\n{alts_str}\n"
        )

        messages = [
            LLMMessage(role="system", content=SYSTEM_PROMPT),
            LLMMessage(role="user", content=user_prompt),
        ]

        result: SensitivityAnalysisOutput = await execute_structured_prompt(
            provider=self.provider,
            messages=messages,
            schema=SensitivityAnalysisOutput,
        )

        findings = [
            AgentFinding(
                case_id=case.case_id,
                task_id=generate_id("TASK-SENS"),
                agent="sensitivity_engine",
                target_id=case.proposed_decision,
                status=f"ROBUSTNESS_{result.robustness_score:.2f}",
                reason=f"Tested {len(result.scenarios)} What-If scenarios. Robustness: {result.robustness_score:.2f}",
                confidence=result.robustness_score,
                metadata={
                    "fragile_assumptions": result.most_fragile_assumptions,
                    "thresholds": result.critical_cost_or_risk_thresholds,
                },
            )
        ]

        return result, findings
