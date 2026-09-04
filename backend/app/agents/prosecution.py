"""
Prosecution Agent.
Implements Module 16 (Prosecution Agent).
Acts as opposition counsel, surfacing credible counterarguments, hidden costs, weak assumptions,
and critical failure modes without fabricating facts.
"""

from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from app.schemas.entities import DecisionCase, AgentFinding, generate_id
from app.schemas.court import Argument
from app.services.llm_provider import BaseLLMProvider, LLMMessage, execute_structured_prompt


class ProsecutionArgumentItem(BaseModel):
    title: str
    target_claim_id: Optional[str] = None
    target_assumption_id: Optional[str] = None
    statement: str = Field(description="The concrete counterargument or prosecution challenge")
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    severity_or_strength: float = Field(default=0.8, ge=0.0, le=1.0)
    challenge_category: str = Field(
        default="Counter-evidence",
        description="Counter-evidence, Weak assumption, Missing evidence, Hidden cost, Failure mode, or Unconsidered constraint"
    )


class ProsecutionBatchOutput(BaseModel):
    prosecution_case_summary: str
    arguments: List[ProsecutionArgumentItem] = Field(default_factory=list)
    critical_vulnerabilities: List[str] = Field(default_factory=list)


SYSTEM_PROMPT = """You are the Prosecution Agent in the Multi-Agent Decision Court.
Your responsibility:
1. Act as rigorous opposition counsel challenging the proposed decision.
2. Attack ungrounded claims, unverified assumptions, hidden financial/operational costs, and single points of failure.
3. Highlight missing evidence and demonstrate how the decision could fail in practice.
4. CRITICAL: Do NOT fabricate facts or counter-evidence. Base all challenges on analytical weaknesses, logic flaws, or provided evidence.
"""


class ProsecutionAgent:
    def __init__(self, provider: BaseLLMProvider):
        self.provider = provider

    async def prosecute_case(
        self, case: DecisionCase, findings_context: Optional[List[AgentFinding]] = None
    ) -> Tuple[ProsecutionBatchOutput, List[Argument], List[AgentFinding]]:
        claims_str = "\n".join([f"[{c.claim_id}] {c.statement} (Status: {c.status.value})" for c in case.claims])
        assumptions_str = "\n".join([f"[{a.assumption_id}] {a.statement} (Status: {a.status.value})" for a in case.assumptions])
        risks_str = "\n".join([f"[{r.risk_id}] {r.description}" for r in case.risks])
        
        findings_str = ""
        if findings_context:
            findings_str = "\nPRIOR AGENT FINDINGS:\n" + "\n".join([
                f"- [{f.agent}] Target {f.target_id}: {f.reason} (Status: {f.status})"
                for f in findings_context[:10]
            ])

        user_prompt = (
            f"Case Title: {case.title}\n"
            f"Problem Statement: {case.problem}\n"
            f"Proposed Decision: {case.proposed_decision}\n\n"
            f"CLAIMS:\n{claims_str}\n\n"
            f"ASSUMPTIONS:\n{assumptions_str}\n\n"
            f"IDENTIFIED RISKS:\n{risks_str}\n"
            f"{findings_str}\n"
        )

        messages = [
            LLMMessage(role="system", content=SYSTEM_PROMPT),
            LLMMessage(role="user", content=user_prompt),
        ]

        result: ProsecutionBatchOutput = await execute_structured_prompt(
            provider=self.provider,
            messages=messages,
            schema=ProsecutionBatchOutput,
        )

        arguments = []
        agent_findings = []

        for arg in result.arguments:
            argument_obj = Argument(
                arg_id=generate_id("ARG-PROS"),
                side="PROSECUTION",
                title=arg.title,
                target_claim_id=arg.target_claim_id,
                target_assumption_id=arg.target_assumption_id,
                statement=arg.statement,
                supporting_evidence_ids=arg.supporting_evidence_ids,
                confidence=arg.confidence,
                severity_or_strength=arg.severity_or_strength,
            )
            arguments.append(argument_obj)
            
            agent_findings.append(
                AgentFinding(
                    case_id=case.case_id,
                    task_id=generate_id("TASK-PROS"),
                    agent="prosecution",
                    target_id=arg.target_claim_id or arg.target_assumption_id or case.proposed_decision,
                    status="CHALLENGED",
                    reason=f"[{arg.challenge_category}] {arg.title}: {arg.statement}",
                    confidence=arg.confidence,
                    requires_followup=True,
                    metadata={"category": arg.challenge_category, "severity": arg.severity_or_strength},
                )
            )

        return result, arguments, agent_findings
