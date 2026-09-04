"""
Core Domain Entities Schema for Multi-Agent Decision Court.
Implements Modules 3, 6, 7, 10, 11, 12, 14, 15, 18, 19, 32.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict
import uuid

from app.schemas.enums import (
    ProvenanceType,
    ClaimSupportStatus,
    AssumptionStatus,
    RequirementStatus,
    ReconciliationStatus,
    NodeType,
    EdgeType,
    RiskCategory,
)


def generate_id(prefix: str = "obj") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


# Module 6: Evidence & Provenance
class Evidence(BaseModel):
    evidence_id: str = Field(default_factory=lambda: generate_id("E"))
    source_type: ProvenanceType = ProvenanceType.USER_PROVIDED
    source_reference: Optional[str] = None
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    author: Optional[str] = None
    reliability: float = Field(default=0.7, ge=0.0, le=1.0)
    relevance: float = Field(default=0.8, ge=0.0, le=1.0)
    strength: float = Field(default=0.7, ge=0.0, le=1.0)
    claims_supported: List[str] = Field(default_factory=list)
    claims_contradicted: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


# Module 10: Claim Decomposer
class Claim(BaseModel):
    claim_id: str = Field(default_factory=lambda: generate_id("C"))
    statement: str
    category: Optional[str] = None
    status: ClaimSupportStatus = ClaimSupportStatus.UNKNOWN
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    contradicting_evidence_ids: List[str] = Field(default_factory=list)
    is_core_decision_claim: bool = False
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# Module 12: Assumption Auditor
class Assumption(BaseModel):
    assumption_id: str = Field(default_factory=lambda: generate_id("A"))
    statement: str
    is_explicit: bool = True
    status: AssumptionStatus = AssumptionStatus.UNVERIFIED
    dependent_claim_ids: List[str] = Field(default_factory=list)
    validity_score: float = Field(default=0.5, ge=0.0, le=1.0)
    criticality: float = Field(default=0.5, ge=0.0, le=1.0, description="How sensitive is the decision if this fails")
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# Module 14: Requirement Validator
class Requirement(BaseModel):
    req_id: str = Field(default_factory=lambda: generate_id("R"))
    description: str
    is_critical: bool = False
    is_constraint: bool = False
    status: RequirementStatus = RequirementStatus.UNKNOWN
    satisfaction_score: float = Field(default=0.0, ge=0.0, le=1.0)
    violating_factors: List[str] = Field(default_factory=list)
    supporting_factors: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# Module 15: Theory Analyst
class Theory(BaseModel):
    theory_id: str = Field(default_factory=lambda: generate_id("T"))
    name: str
    preconditions: List[str] = Field(default_factory=list)
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    contradicting_evidence_ids: List[str] = Field(default_factory=list)
    applicability_score: float = Field(default=0.5, ge=0.0, le=1.0)
    limitations: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    model_config = ConfigDict(from_attributes=True)


# Module 18: Risk Analyst
class Risk(BaseModel):
    risk_id: str = Field(default_factory=lambda: generate_id("RISK"))
    category: RiskCategory = RiskCategory.UNKNOWN
    description: str
    probability: float = Field(default=0.5, ge=0.0, le=1.0)
    impact: float = Field(default=0.5, ge=0.0, le=1.0)
    severity_score: float = Field(default=0.25, ge=0.0, le=1.0)
    mitigation_suggested: Optional[str] = None
    affected_claim_ids: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# Module 19: Alternative Generator
class Alternative(BaseModel):
    alt_id: str = Field(default_factory=lambda: generate_id("ALT"))
    title: str
    description: str
    category: str = Field(default="Alternative approach")
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)
    estimated_feasibility: float = Field(default=0.5, ge=0.0, le=1.0)
    requirement_fit_score: float = Field(default=0.5, ge=0.0, le=1.0)

    model_config = ConfigDict(from_attributes=True)


# Module 7: Decision Graph Schema
class DecisionGraphNode(BaseModel):
    id: str
    label: str
    node_type: NodeType
    properties: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0


class DecisionGraphEdge(BaseModel):
    source: str
    target: str
    relation: EdgeType
    weight: float = 1.0
    properties: Dict[str, Any] = Field(default_factory=dict)


class DecisionGraphData(BaseModel):
    nodes: List[DecisionGraphNode] = Field(default_factory=list)
    edges: List[DecisionGraphEdge] = Field(default_factory=list)


# Module 32: Agent Communication Protocol
class AgentFinding(BaseModel):
    case_id: str
    task_id: str
    agent: str
    target_id: Optional[str] = None
    status: str
    evidence_ids: List[str] = Field(default_factory=list)
    reason: str
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    requires_followup: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(from_attributes=True)


# Module 3: Universal Case Input
class DecisionCase(BaseModel):
    case_id: str = Field(default_factory=lambda: generate_id("CASE"))
    title: str = "Untitled Decision Case"
    problem: str
    proposed_decision: str
    context: Optional[str] = None
    initial_analysis: Optional[str] = None
    reasoning: Optional[str] = None
    
    requirements: List[Requirement] = Field(default_factory=list)
    constraints: List[Requirement] = Field(default_factory=list)
    claims: List[Claim] = Field(default_factory=list)
    evidence: List[Evidence] = Field(default_factory=list)
    theories: List[Theory] = Field(default_factory=list)
    assumptions: List[Assumption] = Field(default_factory=list)
    observations: List[str] = Field(default_factory=list)
    risks: List[Risk] = Field(default_factory=list)
    alternatives: List[Alternative] = Field(default_factory=list)
    expected_outcomes: List[str] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    version: int = 1

    model_config = ConfigDict(from_attributes=True)
