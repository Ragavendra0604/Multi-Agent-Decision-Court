"""
Tests for Adversarial Court Layer (Modules 16, 17, 20, 21).
"""

import pytest
from app.schemas.enums import (
    ProvenanceType,
    ClaimSupportStatus,
    ReconciliationStatus,
)
from app.schemas.entities import (
    DecisionCase,
    Claim,
    Evidence,
    Assumption,
    Requirement,
)
from app.services.llm_provider import MockLLMProvider
from app.agents.prosecution import ProsecutionAgent
from app.agents.defense import DefenseAgent
from app.agents.cross_examiner import CrossExaminationEngine
from app.evidence.reconciliation import EvidenceReconciliationEngine


@pytest.fixture
def adversarial_case():
    c1 = Claim(claim_id="C-01", statement="Solution X provides 3x throughput", is_core_decision_claim=True)
    c2 = Claim(claim_id="C-02", statement="Solution X reduces overall operational cost", is_core_decision_claim=True)
    e1 = Evidence(evidence_id="E-01", content="Benchmark confirms 3x latency reduction", source_type=ProvenanceType.DOCUMENT_DERIVED)
    e2 = Evidence(evidence_id="E-02", content="Pricing sheet dated Q4 2025 shows 25% higher egress charges", source_type=ProvenanceType.SOURCE_VERIFIED)
    
    return DecisionCase(
        case_id="CASE-ADV-01",
        title="Solution X Deployment",
        problem="Bottlenecks in current database tier",
        proposed_decision="Migrate primary database to Solution X",
        claims=[c1, c2],
        evidence=[e1, e2],
    )


@pytest.mark.asyncio
async def test_prosecution_agent(adversarial_case):
    provider = MockLLMProvider("mock")
    agent = ProsecutionAgent(provider)
    output, args, findings = await agent.prosecute_case(adversarial_case)
    
    assert len(args) >= 1
    assert args[0].side == "PROSECUTION"
    assert len(findings) >= 1
    assert findings[0].agent == "prosecution"


@pytest.mark.asyncio
async def test_defense_agent(adversarial_case):
    provider = MockLLMProvider("mock")
    agent = DefenseAgent(provider)
    output, args, findings = await agent.defend_case(adversarial_case)
    
    assert len(args) >= 1
    assert args[0].side == "DEFENSE"
    assert len(output.concessions_made) >= 1
    assert len(findings) >= 1
    assert findings[0].agent == "defense"


@pytest.mark.asyncio
async def test_cross_examination_engine(adversarial_case):
    provider = MockLLMProvider("mock")
    pros_agent = ProsecutionAgent(provider)
    def_agent = DefenseAgent(provider)
    
    _, pros_args, _ = await pros_agent.prosecute_case(adversarial_case)
    _, def_args, _ = await def_agent.defend_case(adversarial_case)
    
    cross_engine = CrossExaminationEngine(provider, max_rounds=2)
    turns, findings = await cross_engine.cross_examine_claim(
        adversarial_case,
        adversarial_case.claims[0],
        pros_args,
        def_args,
    )
    
    assert len(turns) >= 1
    assert len(findings) == 1
    assert findings[0].agent == "cross_examiner"


@pytest.mark.asyncio
async def test_evidence_reconciliation(adversarial_case):
    provider = MockLLMProvider("mock")
    engine = EvidenceReconciliationEngine(provider)
    
    items, findings = await engine.reconcile_conflicts(
        adversarial_case,
        adversarial_case.evidence,
    )
    
    assert len(items) >= 1
    assert items[0].status == ReconciliationStatus.PARTIALLY_RESOLVED
    assert len(findings) >= 1
    assert findings[0].agent == "reconciliation"
