"""
Comprehensive Evaluation Benchmark & Edge Cases Suite.
Implements Module 48 (Observability), Module 49 (Edge Cases),
Module 50 (Evaluation Framework), and Module 52 (Complete Decision Flow Example).
"""

import pytest
from app.schemas.enums import (
    ProvenanceType,
    VerdictStatus,
    ClaimSupportStatus,
    RequirementStatus,
)
from app.schemas.entities import (
    DecisionCase,
    Claim,
    Evidence,
    Assumption,
    Requirement,
    Risk,
)
from app.services.llm_provider import MockLLMProvider
from app.orchestration.court_orchestrator import CourtOrchestrator


@pytest.mark.asyncio
async def test_module_52_complete_decision_flow():
    """
    Evaluates Section 54 / Module 52 from the specification:
    Should we replace current system with Solution X?
    Requirements: Lower cost, Better performance, Minimal migration risk.
    Evidence: Benchmark says X is 40% faster.
    Expected: PARTIALLY_VALID (Performance supported, but cost reduction and migration feasibility insufficiently supported).
    """
    case = DecisionCase(
        case_id="CASE-M52-01",
        title="Replace Legacy System with Solution X",
        problem="Current system is expensive and slow",
        proposed_decision="Replace with Solution X",
        requirements=[
            Requirement(req_id="R-01", description="Lower cost", is_critical=True),
            Requirement(req_id="R-02", description="Better performance", is_critical=True),
            Requirement(req_id="R-03", description="Minimal migration risk", is_critical=False),
        ],
        claims=[
            Claim(claim_id="C-01", statement="Solution X is 40% faster", is_core_decision_claim=True),
            Claim(claim_id="C-02", statement="Faster system means lower cost", is_core_decision_claim=True),
        ],
        evidence=[
            Evidence(evidence_id="E-01", content="Benchmark says X is 40% faster", source_type=ProvenanceType.DOCUMENT_DERIVED),
        ],
        assumptions=[
            Assumption(assumption_id="A-01", statement="Migration takes only one month", criticality=0.8),
        ],
    )

    provider = MockLLMProvider("mock")
    orchestrator = CourtOrchestrator(provider=provider)

    result = await orchestrator.execute_court_session(case)

    # Verify Module 52 expected outcome: PARTIALLY_VALID
    assert result.verdict.verdict == VerdictStatus.PARTIALLY_VALID
    assert result.verdict.decision_correctness.status.value in ("LIKELY_VALID", "DEFINITELY_CORRECT", "UNCERTAIN")
    assert result.verdict.decision_justification.status.value in ("PARTIAL", "INSUFFICIENT")
    assert len(result.report.markdown_content) > 500
    assert len(result.findings) >= 8


@pytest.mark.asyncio
async def test_module_49_edge_case_no_evidence():
    """
    Module 49 Edge Case: No evidence -> Confidence lowered / marked insufficient.
    """
    case = DecisionCase(
        case_id="CASE-NO-EV",
        title="Hasty Framework Migration",
        problem="Team feels current tech stack is boring",
        proposed_decision="Rewrite entire codebase in newly launched language",
        claims=[
            Claim(claim_id="C-01", statement="New language will boost morale by 100%"),
        ],
        evidence=[],  # No evidence
        requirements=[
            Requirement(req_id="R-01", description="Maintain feature parity within 1 quarter", is_critical=True),
        ],
    )

    provider = MockLLMProvider("mock")
    orchestrator = CourtOrchestrator(provider=provider)
    result = await orchestrator.execute_court_session(case)

    assert result.verdict.confidence <= 0.85
    assert len(result.verdict.missing_information) >= 1 or len(result.verdict.unresolved_questions) >= 1
