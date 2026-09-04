"""
Defense Agent.
Implements Module 17 (Defense Agent).
Advocates for the proposed decision using grounded evidence, while transparently conceding
unsupported weaknesses.
"""

from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from app.schemas.entities import DecisionCase, AgentFinding, generate_id
from app.schemas.court import Argument
from app.services.llm_provider import BaseLLMProvider, LLMMessage, execute_structured_prompt


class DefenseArgumentItem(BaseModel):
    title: str
    target_claim_id: Optional[str] = None
    statement: str = Field(description="The concrete defense argument or rebuttal")
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    severity_or_strength: float = Field(default=0.8, ge=0.0, le=1.0)
    defense_strategy: str = Field(
        default="Direct evidence backing",
        description="Direct evidence backing, Mitigation feasibility, Comparative superiority, or Controlled concession"
    )


class ConcessionItem(BaseModel):
    weakness_area: str
    concession_summary: str
    mitigation_or_contingency: str


class DefenseBatchOutput(BaseModel):
    defense_case_summary: str
    arguments: List[DefenseArgumentItem] = Field(default_factory=list)
    concessions_made: List[ConcessionItem] = Field(default_factory=list)


SYSTEM_PROMPT = """You are the Defense Agent in the Multi-Agent Decision Court.
Your responsibility:
1. Build the strongest factual case in defense of the proposed decision.
2. Ground all defense arguments in available evidence and validated requirements.
3. Offer constructive mitigations to risks raised by prosecution.
4. RULE: Concede transparently when evidence is missing or weak rather than making unfounded claims.
"""


class DefenseAgent:
    def __init__(self, provider: BaseLLMProvider):
        self.provider = provider

    async def defend_case(
        self,
        case: DecisionCase,
        prosecution_arguments: Optional[List[Argument]] = None,
        findings_context: Optional[List[AgentFinding]] = None,
    ) -> Tuple[DefenseBatchOutput, List[Argument], List[AgentFinding]]:
        claims_str = "\n".join([f"[{c.claim_id}] {c.statement}" for c in case.claims])
        ev_str = "\n".join([f"[{e.evidence_id}] {e.content} (Reliability: {e.reliability})" for e in case.evidence])
        
        pros_str = ""
        if prosecution_arguments:
            pros_str = "\nPROSECUTION CHALLENGES TO REBUT:\n" + "\n".join([
                f"- [{p.title}] Target: {p.target_claim_id or 'Decision'}: {p.statement}"
                for p in prosecution_arguments
            ])

        user_prompt = (
            f"Case: {case.title}\n"
            f"Decision Under Defense: {case.proposed_decision}\n\n"
            f"SUPPORTING CLAIMS:\n{claims_str}\n\n"
            f"AVAILABLE EVIDENCE:\n{ev_str}\n"
            f"{pros_str}\n"
        )

        messages = [
            LLMMessage(role="system", content=SYSTEM_PROMPT),
            LLMMessage(role="user", content=user_prompt),
        ]

        result: DefenseBatchOutput = await execute_structured_prompt(
            provider=self.provider,
            messages=messages,
            schema=DefenseBatchOutput,
        )

        arguments = []
        agent_findings = []

        for arg in result.arguments:
            argument_obj = Argument(
                arg_id=generate_id("ARG-DEF"),
                side="DEFENSE",
                title=arg.title,
                target_claim_id=arg.target_claim_id,
                statement=arg.statement,
                supporting_evidence_ids=arg.supporting_evidence_ids,
                confidence=arg.confidence,
                severity_or_strength=arg.severity_or_strength,
            )
            arguments.append(argument_obj)
            
            agent_findings.append(
                AgentFinding(
                    case_id=case.case_id,
                    task_id=generate_id("TASK-DEF"),
                    agent="defense",
                    target_id=arg.target_claim_id or case.proposed_decision,
                    status="DEFENDED",
                    reason=f"[{arg.defense_strategy}] {arg.title}: {arg.statement}",
                    confidence=arg.confidence,
                    metadata={"strategy": arg.defense_strategy, "strength": arg.severity_or_strength},
                )
            )

        return result, arguments, agent_findings
