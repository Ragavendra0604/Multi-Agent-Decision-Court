"""
Judge Agent & Verdict Adjudication Engine.
Implements Module 24 (Judge Agent), Module 25 (Verdict Model), and Module 53 (Final Verdict Schema).
Impartially synthesizes all analytical findings, adversarial debates, and evidence reconciliations,
separately scoring Decision Correctness vs Decision Justification without majority voting.
"""

from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from app.schemas.enums import (
    VerdictStatus,
    DecisionCorrectnessStatus,
    DecisionJustificationStatus,
    RequirementStatus,
)
from app.schemas.entities import (
    DecisionCase,
    AgentFinding,
    generate_id,
)
from app.schemas.court import (
    Argument,
    CrossExaminationTurn,
    ReconciledEvidenceItem,
    DecisionCorrectness,
    DecisionJustification,
    Verdict,
)
from app.services.llm_provider import BaseLLMProvider, LLMMessage, execute_structured_prompt


class JudgeOutputSchema(BaseModel):
    verdict: VerdictStatus = Field(
        description="VALID, PARTIALLY_VALID, INVALID, INSUFFICIENT_EVIDENCE, INCONCLUSIVE, HIGH_RISK, or REQUIRES_HUMAN_REVIEW"
    )
    confidence: float = Field(default=0.75, ge=0.0, le=1.0)
    
    correctness_status: DecisionCorrectnessStatus = Field(default=DecisionCorrectnessStatus.UNCERTAIN)
    correctness_confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    correctness_summary: str = Field(description="Evaluation of whether the decision outcome is likely right")
    
    justification_status: DecisionJustificationStatus = Field(default=DecisionJustificationStatus.INSUFFICIENT)
    justification_confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    justification_summary: str = Field(description="Evaluation of whether the arguments & evidence presented justify the choice")
    
    summary_verdict_rationale: str
    critical_decision_drivers: List[str] = Field(default_factory=list)
    unresolved_questions: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    recommended_next_actions: List[str] = Field(default_factory=list)


JUDGE_SYSTEM_PROMPT = """You are the Supreme Judge in the Multi-Agent Decision Court.
Your responsibility:
1. Synthesize all findings: Requirements, Evidence, Assumptions, Logic flaws, Risks, Alternatives, Prosecution arguments, Defense arguments, Cross-examinations, and Reconciliations.
2. DO NOT use majority voting among agents. Adjudicate based on evidence strength, logic soundness, and requirement satisfaction.
3. SEPARATELY EVALUATE:
   - Decision Correctness: Is the proposed action likely a good idea in practice?
   - Decision Justification: Did the proponent actually prove or justify it with valid facts and reasoning?
4. Assign a final Verdict:
   - VALID: Fully supported by evidence, logic sound, critical requirements met.
   - PARTIALLY_VALID: Key elements supported, but some assumptions/costs unproven.
   - INVALID: Disproven by evidence or violates non-negotiable constraints.
   - INSUFFICIENT_EVIDENCE: Core claims lack any empirical proof.
   - INCONCLUSIVE: Conflicting evidence or deep empirical uncertainty.
   - HIGH_RISK: Substantial severity risks outweigh potential benefits.
   - REQUIRES_HUMAN_REVIEW: Consequential policy impact or high-stakes ethical/financial dilemma.
5. Provide actionable Recommended Next Actions (e.g. pilot tests, independent audits, metric gathering).
"""


class JudgeAgent:
    def __init__(self, provider: BaseLLMProvider):
        self.provider = provider

    async def adjudicate(
        self,
        case: DecisionCase,
        findings: List[AgentFinding],
        prosecution_arguments: List[Argument],
        defense_arguments: List[Argument],
        cross_examinations: List[CrossExaminationTurn],
        reconciliations: List[ReconciledEvidenceItem],
    ) -> Tuple[Verdict, List[AgentFinding]]:
        # Check for immediate critical constraint violations
        has_critical_failure = any(
            (r.is_constraint or r.is_critical) and r.status == RequirementStatus.UNSATISFIED
            for r in case.requirements + case.constraints
        )

        valid_findings = [f for f in findings if f.status != "ERROR"]
        if not valid_findings:
            valid_findings = findings[:8]
        else:
            valid_findings = valid_findings[:10]

        findings_summary = "\n".join([
            f"- [{f.agent}] {f.reason[:120]} (Status: {f.status})"
            for f in valid_findings
        ]) or "No agent findings recorded."

        arguments_summary = "PROSECUTION:\n" + "\n".join([
            f"- {a.title}: {a.statement[:160]}"
            for a in prosecution_arguments[:4]
        ]) + "\n\nDEFENSE:\n" + "\n".join([
            f"- {a.title}: {a.statement[:160]}"
            for a in defense_arguments[:4]
        ])

        cross_summary = "\n".join([
            f"- Turn {t.round_number} on {t.target_claim_id}: Prosecution: {t.challenge} | Defense: {t.defense_response} | Result: {t.resolution_state}"
            for t in cross_examinations
        ]) or "No cross-examination turns."

        reconcile_summary = "\n".join([
            f"- {r.topic_or_claim_id}: Status {r.status.value}. Rationale: {r.resolution_rationale}"
            for r in reconciliations
        ]) or "No conflicting evidence items required reconciliation."

        user_prompt = (
            f"=== CASE UNDER ADJUDICATION ===\n"
            f"Title: {case.title}\n"
            f"Problem: {case.problem}\n"
            f"Proposed Decision: {case.proposed_decision}\n"
            f"Context: {case.context or 'N/A'}\n\n"
            f"=== COURT FINDINGS ===\n{findings_summary}\n\n"
            f"=== ADVERSARIAL ARGUMENTS ===\n{arguments_summary}\n\n"
            f"=== CROSS EXAMINATION RECORD ===\n{cross_summary}\n\n"
            f"=== EVIDENCE RECONCILIATION RECORD ===\n{reconcile_summary}\n\n"
            f"Critical Constraint Failure Detected Programmatically: {has_critical_failure}\n"
        )

        messages = [
            LLMMessage(role="system", content=JUDGE_SYSTEM_PROMPT),
            LLMMessage(role="user", content=user_prompt),
        ]

        result: JudgeOutputSchema = await execute_structured_prompt(
            provider=self.provider,
            messages=messages,
            schema=JudgeOutputSchema,
        )

        # Enforce critical constraint override rule
        final_verdict_status = result.verdict
        if has_critical_failure and final_verdict_status == VerdictStatus.VALID:
            final_verdict_status = VerdictStatus.PARTIALLY_VALID

        verdict_obj = Verdict(
            verdict_id=generate_id("VERDICT"),
            case_id=case.case_id,
            verdict=final_verdict_status,
            confidence=result.confidence,
            decision_correctness=DecisionCorrectness(
                status=result.correctness_status,
                confidence=result.correctness_confidence,
                summary=result.correctness_summary,
            ),
            decision_justification=DecisionJustification(
                status=result.justification_status,
                confidence=result.justification_confidence,
                summary=result.justification_summary,
            ),
            summary_verdict_rationale=result.summary_verdict_rationale,
            requirements=case.requirements + case.constraints,
            claims=case.claims,
            evidence=case.evidence,
            assumptions=case.assumptions,
            risks=case.risks,
            counterarguments=prosecution_arguments,
            defense_arguments=defense_arguments,
            alternatives=case.alternatives,
            unresolved_questions=result.unresolved_questions,
            missing_information=result.missing_information,
            critical_decision_drivers=result.critical_decision_drivers,
            recommended_next_actions=result.recommended_next_actions,
        )

        judge_findings = [
            AgentFinding(
                case_id=case.case_id,
                task_id=generate_id("TASK-JUDGE"),
                agent="judge",
                target_id=case.proposed_decision,
                status=verdict_obj.verdict.value,
                reason=f"Verdict: {verdict_obj.verdict.value}. Justification: {verdict_obj.decision_justification.status.value}",
                confidence=verdict_obj.confidence,
                requires_followup=verdict_obj.verdict in (
                    VerdictStatus.REQUIRES_HUMAN_REVIEW,
                    VerdictStatus.HIGH_RISK,
                    VerdictStatus.INSUFFICIENT_EVIDENCE,
                ),
                metadata={
                    "correctness": verdict_obj.decision_correctness.status.value,
                    "justification": verdict_obj.decision_justification.status.value,
                    "drivers": verdict_obj.critical_decision_drivers,
                },
            )
        ]

        return verdict_obj, judge_findings
