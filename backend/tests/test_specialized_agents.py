"""
Tests for Specialized Analytical Agents (Modules 9, 10, 11, 12, 13, 14, 15, 18, 19).
"""

import pytest
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
)
from app.services.llm_provider import MockLLMProvider
from app.agents.case_analyst import CaseAnalystAgent
from app.agents.evidence_investigator import EvidenceInvestigatorAgent
from app.agents.assumption_auditor import AssumptionAuditorAgent
from app.agents.logic_analyst import LogicAnalystAgent
from app.agents.requirement_validator import RequirementValidatorAgent
from app.agents.theory_analyst import TheoryAnalystAgent
from app.agents.risk_analyst import RiskAnalystAgent
from app.agents.alternative_generator import AlternativeGeneratorAgent


@pytest.fixture
def sample_case():
    return DecisionCase(
        case_id="CASE-TEST-1",
        title="Migrate Backend to Solution X",
        problem="High database latency and slow query throughput",
        proposed_decision="Migrate primary database to Solution X",
        claims=[
            Claim(claim_id="C-01", statement="Solution X reduces latency by 40%", is_core_decision_claim=True),
            Claim(claim_id="C-02", statement="Solution X is overall cheaper", is_core_decision_claim=True),
        ],
        evidence=[
            Evidence(evidence_id="E-01", content="Benchmark report shows 40% latency drop", source_type=ProvenanceType.DOCUMENT_DERIVED),
            Evidence(evidence_id="E-02", content="Pricing sheet shows higher egress cost", source_type=ProvenanceType.SOURCE_VERIFIED),
        ],
        assumptions=[
            Assumption(assumption_id="A-01", statement="Staff can transition without retraining", is_explicit=True),
        ],
        requirements=[
            Requirement(req_id="R-01", description="Keep migration budget under $100k", is_critical=True, is_constraint=True),
        ],
        theories=[
            Theory(theory_id="T-01", name="Horizontal scaling economy", preconditions=["Stateless app architecture"]),
        ],
        risks=[
            Risk(risk_id="RISK-01", description="Vendor lock-in", category=RiskCategory.TECHNICAL, severity_score=0.4),
        ],
    )


@pytest.mark.asyncio
async def test_case_analyst(sample_case):
    provider = MockLLMProvider("mock")
    agent = CaseAnalystAgent(provider)
    output, findings = await agent.analyze(sample_case)
    assert len(output.objective) > 0
    assert len(findings) == 1
    assert findings[0].agent == "case_analyst"


@pytest.mark.asyncio
async def test_evidence_investigator(sample_case):
    provider = MockLLMProvider("mock")
    agent = EvidenceInvestigatorAgent(provider)
    investigations, findings = await agent.investigate_claims(sample_case)
    assert len(investigations) >= 1
    assert any(i.status == ClaimSupportStatus.SUPPORTED for i in investigations)
    assert len(findings) >= 1


@pytest.mark.asyncio
async def test_assumption_auditor(sample_case):
    provider = MockLLMProvider("mock")
    agent = AssumptionAuditorAgent(provider)
    output, findings = await agent.audit_assumptions(sample_case)
    assert len(output.audited_assumptions) >= 1
    assert len(output.uncovered_hidden_assumptions) >= 1
    assert len(findings) >= 1


@pytest.mark.asyncio
async def test_logic_analyst(sample_case):
    provider = MockLLMProvider("mock")
    agent = LogicAnalystAgent(provider)
    output, findings = await agent.analyze_logic(sample_case)
    assert output.reasoning_structure_soundness in ("SOUND", "WEAK", "FLAWED", "INVALID")
    assert len(findings) == 1


@pytest.mark.asyncio
async def test_requirement_validator(sample_case):
    provider = MockLLMProvider("mock")
    agent = RequirementValidatorAgent(provider)
    output, findings = await agent.validate_requirements(sample_case)
    assert len(output.evaluations) >= 1
    assert len(findings) >= 1


@pytest.mark.asyncio
async def test_theory_analyst(sample_case):
    provider = MockLLMProvider("mock")
    agent = TheoryAnalystAgent(provider)
    output, findings = await agent.analyze_theories(sample_case)
    assert len(output.evaluations) >= 1
    assert len(findings) >= 1


@pytest.mark.asyncio
async def test_risk_analyst(sample_case):
    provider = MockLLMProvider("mock")
    agent = RiskAnalystAgent(provider)
    output, findings = await agent.analyze_risks(sample_case)
    assert len(output.identified_risks) >= 1
    assert len(findings) >= 1


@pytest.mark.asyncio
async def test_alternative_generator(sample_case):
    provider = MockLLMProvider("mock")
    agent = AlternativeGeneratorAgent(provider)
    output, findings = await agent.generate_alternatives(sample_case)
    assert len(output.alternatives) >= 1
    assert len(output.decision_matrix) >= 1
    assert len(findings) >= 1
