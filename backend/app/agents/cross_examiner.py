"""
Cross-Examination Engine.
Implements Module 20 (Cross-Examination Engine).
Orchestrates structured multi-round adversarial debates between Prosecution and Defense on contentious claims,
terminating when resolved or max rounds reached.
"""

from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from app.config import settings
from app.schemas.entities import DecisionCase, Claim, AgentFinding, generate_id
from app.schemas.court import Argument, CrossExaminationTurn
from app.services.llm_provider import BaseLLMProvider, LLMMessage, execute_structured_prompt


class CrossExamTurnOutput(BaseModel):
    challenge: str = Field(description="Prosecution challenge regarding the claim")
    defense_response: str = Field(description="Defense rebuttal grounded in evidence")
    counter_challenge: Optional[str] = Field(default=None, description="Prosecution rejoinder or follow-up")
    resolution_state: str = Field(default="PARTIALLY_RESOLVED", description="RESOLVED, PARTIALLY_RESOLVED, or UNRESOLVED")
    unresolved_uncertainty: Optional[str] = Field(default=None, description="Remaining empirical or logical gap")
    terminate_debate: bool = Field(default=False, description="True if conflict is settled or no new arguments remain")


SYSTEM_PROMPT = """You are the Cross-Examination Adjudicator for the Multi-Agent Decision Court.
Your responsibility:
1. Conduct an adversarial cross-examination round between Prosecution and Defense on a specific disputed claim.
2. Structure the exchange:
   - Challenge (Prosecution attacks claim/evidence)
   - Defense Response (Defense counters with facts/mitigations)
   - Counter-challenge (Prosecution attacks the defense response)
   - Resolution Status (RESOLVED, PARTIALLY_RESOLVED, UNRESOLVED)
3. Set terminate_debate=True if the issue is completely settled or if further debate is purely repetitive.
"""


class CrossExaminationEngine:
    def __init__(self, provider: BaseLLMProvider, max_rounds: Optional[int] = None):
        self.provider = provider
        self.max_rounds = max_rounds or settings.MAX_DEBATE_ROUNDS

    async def cross_examine_claim(
        self,
        case: DecisionCase,
        claim: Claim,
        prosecution_arguments: List[Argument],
        defense_arguments: List[Argument],
    ) -> Tuple[List[CrossExaminationTurn], List[AgentFinding]]:
        turns: List[CrossExaminationTurn] = []
        findings: List[AgentFinding] = []

        relevant_pros = [p for p in prosecution_arguments if p.target_claim_id == claim.claim_id or not p.target_claim_id]
        relevant_def = [d for d in defense_arguments if d.target_claim_id == claim.claim_id or not d.target_claim_id]

        for round_idx in range(1, self.max_rounds + 1):
            prior_history = "\n".join([
                f"Round {t.round_number}: Prosecution said: {t.challenge} -> Defense replied: {t.defense_response} -> Counter: {t.counter_challenge}"
                for t in turns
            ]) or "Initial round."

            user_prompt = (
                f"Claim Under Cross-Examination: [{claim.claim_id}] {claim.statement}\n"
                f"Case Decision: {case.proposed_decision}\n"
                f"Debate Round: {round_idx} of {self.max_rounds}\n\n"
                f"Prosecution Arsenal: {[p.statement for p in relevant_pros]}\n"
                f"Defense Arsenal: {[d.statement for d in relevant_def]}\n\n"
                f"Prior Rounds History:\n{prior_history}\n"
            )

            messages = [
                LLMMessage(role="system", content=SYSTEM_PROMPT),
                LLMMessage(role="user", content=user_prompt),
            ]

            result: CrossExamTurnOutput = await execute_structured_prompt(
                provider=self.provider,
                messages=messages,
                schema=CrossExamTurnOutput,
            )

            turn = CrossExaminationTurn(
                turn_id=generate_id(f"TURN-R{round_idx}"),
                round_number=round_idx,
                target_claim_id=claim.claim_id,
                challenge=result.challenge,
                defense_response=result.defense_response,
                counter_challenge=result.counter_challenge,
                resolution_state=result.resolution_state,
                unresolved_uncertainty=result.unresolved_uncertainty,
            )
            turns.append(turn)

            if result.terminate_debate or result.resolution_state == "RESOLVED":
                break

        findings.append(
            AgentFinding(
                case_id=case.case_id,
                task_id=generate_id("TASK-CROSS"),
                agent="cross_examiner",
                target_id=claim.claim_id,
                status=turns[-1].resolution_state if turns else "UNRESOLVED",
                reason=f"Debated over {len(turns)} rounds. Final status: {turns[-1].resolution_state if turns else 'UNRESOLVED'}",
                confidence=0.8,
                metadata={
                    "total_rounds": len(turns),
                    "unresolved_gap": turns[-1].unresolved_uncertainty if turns else None,
                },
            )
        )

        return turns, findings
