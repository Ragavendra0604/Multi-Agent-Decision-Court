"""
Natural Language Case Decomposer Agent.
Implements Module 4 (Case Decomposer), Module 3 (Universal Case Input), and Module 49 (Edge Cases).
Converts free-form human text into a structured DecisionCase graph.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.schemas.enums import (
    ProvenanceType,
    ClaimSupportStatus,
    AssumptionStatus,
    RequirementStatus,
    RiskCategory,
)
from app.schemas.entities import (
    DecisionCase,
    Claim,
    Evidence,
    Assumption,
    Requirement,
    Theory,
    Risk,
    Alternative,
    generate_id,
)
from app.services.llm_provider import (
    BaseLLMProvider,
    LLMMessage,
    execute_structured_prompt,
)
from app.services.structured_output import parse_float_safe


class DecompositionOutputSchema(BaseModel):
    title: str = Field(description="Clear title for the decision case")
    problem: str = Field(description="The underlying problem or decision context")
    proposed_decision: str = Field(description="The specific decision option proposed")
    context: Optional[str] = Field(default=None, description="Relevant background or context")
    initial_analysis: Optional[str] = Field(default=None, description="Initial rationale or thoughts")
    
    requirements: List[str] = Field(default_factory=list, description="Explicit or implicit requirements")
    constraints: List[str] = Field(default_factory=list, description="Budget, time, compliance, or physical constraints")
    
    claims: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Atomic testable claims supporting or opposing the decision. Format: {statement, category, is_core}"
    )
    assumptions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Explicit or hidden assumptions. Format: {statement, is_explicit, criticality (0.0 to 1.0)}"
    )
    theories: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Underlying theories or predictive models cited. Format: {name, preconditions}"
    )
    risks: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Potential failure modes or hazards. Format: {description, category, impact, probability}"
    )
    alternatives: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Viable alternative options mentioned or implied. Format: {title, description, category}"
    )
    missing_information: List[str] = Field(
        default_factory=list,
        description="Crucial missing data or unanswered questions (NEVER invent facts)"
    )


DECOMPOSER_SYSTEM_PROMPT = """You are the Case Decomposer for the Multi-Agent Decision Court.
Your responsibility is to analyze unstructured, human-provided decision text and transform it into structured decision objects.

Rules:
1. Break complex arguments into atomic, testable claims (e.g. "X is cheaper", "X is faster", "X solves Y").
2. Identify both EXPLICIT and HIDDEN assumptions (e.g. assuming staff has necessary skills, assuming prices remain fixed).
3. Extract stated requirements and constraints.
4. If information is missing, list it under missing_information. DO NOT INVENT FACTS.
5. Provide a clear, actionable title, problem statement, and proposed decision.
"""


class CaseDecomposer:
    """
    Decomposes raw user text or structured drafts into fully normalized DecisionCase instances.
    """

    def __init__(self, provider: BaseLLMProvider):
        self.provider = provider

    async def decompose_text(self, raw_user_text: str, case_id: Optional[str] = None) -> DecisionCase:
        messages = [
            LLMMessage(role="system", content=DECOMPOSER_SYSTEM_PROMPT),
            LLMMessage(
                role="user",
                content=f"Decompose the following human decision case:\n\n{raw_user_text}"
            ),
        ]

        structured: DecompositionOutputSchema = await execute_structured_prompt(
            provider=self.provider,
            messages=messages,
            schema=DecompositionOutputSchema,
        )

        target_case_id = case_id or generate_id("CASE")

        # Convert requirements
        req_objects = [
            Requirement(
                req_id=generate_id("R"),
                description=r,
                is_critical=False,
                status=RequirementStatus.UNKNOWN,
            )
            for r in structured.requirements
        ]
        
        # Convert constraints
        constraint_objects = [
            Requirement(
                req_id=generate_id("CST"),
                description=c,
                is_critical=True,
                is_constraint=True,
                status=RequirementStatus.UNKNOWN,
            )
            for c in structured.constraints
        ]

        # Convert claims
        claim_objects = []
        for c in structured.claims:
            stmt = c.get("statement", "")
            if stmt:
                claim_objects.append(
                    Claim(
                        claim_id=generate_id("C"),
                        statement=stmt,
                        category=c.get("category"),
                        is_core_decision_claim=c.get("is_core", True),
                        status=ClaimSupportStatus.UNKNOWN,
                    )
                )

        # Convert assumptions
        assumption_objects = []
        for a in structured.assumptions:
            stmt = a.get("statement", "")
            if stmt:
                assumption_objects.append(
                    Assumption(
                        assumption_id=generate_id("A"),
                        statement=stmt,
                        is_explicit=bool(a.get("is_explicit", False)),
                        criticality=parse_float_safe(a.get("criticality"), 0.5),
                        status=AssumptionStatus.UNVERIFIED,
                    )
                )

        # Convert theories
        theory_objects = []
        for t in structured.theories:
            name = t.get("name", "")
            if name:
                theory_objects.append(
                    Theory(
                        theory_id=generate_id("T"),
                        name=name,
                        preconditions=t.get("preconditions", []),
                    )
                )

        # Convert risks
        risk_objects = []
        for rk in structured.risks:
            desc = rk.get("description", "")
            if desc:
                cat_str = str(rk.get("category", "UNKNOWN")).upper()
                cat = RiskCategory[cat_str] if cat_str in RiskCategory.__members__ else RiskCategory.UNKNOWN
                prob = parse_float_safe(rk.get("probability"), 0.5)
                imp = parse_float_safe(rk.get("impact"), 0.5)
                risk_objects.append(
                    Risk(
                        risk_id=generate_id("RISK"),
                        description=desc,
                        category=cat,
                        probability=prob,
                        impact=imp,
                        severity_score=round(prob * imp, 2),
                    )
                )

        # Convert alternatives
        alt_objects = []
        for alt in structured.alternatives:
            title = alt.get("title", "")
            if title:
                alt_objects.append(
                    Alternative(
                        alt_id=generate_id("ALT"),
                        title=title,
                        description=alt.get("description", title),
                        category=alt.get("category", "Alternative approach"),
                    )
                )

        return DecisionCase(
            case_id=target_case_id,
            title=structured.title or "Decision Evaluation Case",
            problem=structured.problem or raw_user_text[:200],
            proposed_decision=structured.proposed_decision or "Proposed Action",
            context=structured.context,
            initial_analysis=structured.initial_analysis,
            requirements=req_objects,
            constraints=constraint_objects,
            claims=claim_objects,
            assumptions=assumption_objects,
            theories=theory_objects,
            risks=risk_objects,
            alternatives=alt_objects,
        )
