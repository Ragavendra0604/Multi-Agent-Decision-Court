"""
Court Adjudication, Adversarial & Verdict Schemas.
Implements Modules 16, 17, 20, 21, 24, 25, 26, 53.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.enums import (
    VerdictStatus,
    DecisionCorrectnessStatus,
    DecisionJustificationStatus,
    ReconciliationStatus,
)
from app.schemas.entities import (
    Claim,
    Evidence,
    Assumption,
    Requirement,
    Risk,
    Alternative,
    generate_id,
)


class Argument(BaseModel):
    arg_id: str = Field(default_factory=lambda: generate_id("ARG"))
    side: str = Field(description="PROSECUTION or DEFENSE")
    title: str
    target_claim_id: Optional[str] = None
    target_assumption_id: Optional[str] = None
    statement: str
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    severity_or_strength: float = Field(default=0.7, ge=0.0, le=1.0)

    model_config = ConfigDict(from_attributes=True)


class CrossExaminationTurn(BaseModel):
    turn_id: str = Field(default_factory=lambda: generate_id("TURN"))
    round_number: int
    target_claim_id: str
    challenge: str = Field(description="Prosecution challenge")
    defense_response: str = Field(description="Defense rebuttal")
    counter_challenge: Optional[str] = Field(default=None, description="Prosecution follow-up")
    resolution_state: str = Field(default="UNRESOLVED")
    unresolved_uncertainty: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ReconciledEvidenceItem(BaseModel):
    reconciliation_id: str = Field(default_factory=lambda: generate_id("REC"))
    topic_or_claim_id: str
    conflicting_evidence_ids: List[str] = Field(default_factory=list)
    status: ReconciliationStatus = ReconciliationStatus.UNRESOLVED
    resolution_rationale: str
    authority_comparison: Optional[str] = None
    date_comparison: Optional[str] = None
    applicability_comparison: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DecisionCorrectness(BaseModel):
    status: DecisionCorrectnessStatus = DecisionCorrectnessStatus.UNCERTAIN
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    summary: Optional[str] = None


class DecisionJustification(BaseModel):
    status: DecisionJustificationStatus = DecisionJustificationStatus.INSUFFICIENT
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    summary: Optional[str] = None


# Module 53 & 25: Final Verdict Schema
class Verdict(BaseModel):
    verdict_id: str = Field(default_factory=lambda: generate_id("VERDICT"))
    case_id: str
    verdict: VerdictStatus = VerdictStatus.INCONCLUSIVE
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    
    # Separation of Decision Correctness vs Justification (Module 24 / 26 / 53)
    decision_correctness: DecisionCorrectness = Field(default_factory=DecisionCorrectness)
    decision_justification: DecisionJustification = Field(default_factory=DecisionJustification)
    
    summary_verdict_rationale: str = ""
    requirements: List[Requirement] = Field(default_factory=list)
    claims: List[Claim] = Field(default_factory=list)
    evidence: List[Evidence] = Field(default_factory=list)
    assumptions: List[Assumption] = Field(default_factory=list)
    risks: List[Risk] = Field(default_factory=list)
    counterarguments: List[Argument] = Field(default_factory=list)
    defense_arguments: List[Argument] = Field(default_factory=list)
    alternatives: List[Alternative] = Field(default_factory=list)
    unresolved_questions: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    critical_decision_drivers: List[str] = Field(default_factory=list)
    recommended_next_actions: List[str] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(from_attributes=True)


# Module 26: Final Decision Report
class FinalDecisionReport(BaseModel):
    report_id: str = Field(default_factory=lambda: generate_id("REP"))
    case_id: str
    case_title: str
    executive_summary: str
    case_understanding: str
    original_decision: str
    verdict: Verdict
    markdown_content: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
