"""
Unit tests for Foundation Layer (Module 27, 28, 32, 6, 3, 25, 53).
"""

import pytest
from pydantic import BaseModel, Field
from typing import List

from app.schemas.enums import (
    UserRole,
    CaseState,
    ProvenanceType,
    ClaimSupportStatus,
    AssumptionStatus,
    RequirementStatus,
    VerdictStatus,
    DecisionCorrectnessStatus,
    DecisionJustificationStatus,
    NodeType,
    EdgeType,
)
from app.schemas.entities import (
    Evidence,
    Claim,
    Assumption,
    Requirement,
    DecisionCase,
    DecisionGraphNode,
    DecisionGraphEdge,
    AgentFinding,
)
from app.schemas.court import (
    Verdict,
    DecisionCorrectness,
    DecisionJustification,
    Argument,
)
from app.services.structured_output import (
    extract_json_candidate,
    repair_common_json_issues,
    parse_and_validate_json,
)
from app.services.llm_provider import (
    MockLLMProvider,
    LLMMessage,
    get_llm_provider,
    execute_structured_prompt,
)


class SampleSchema(BaseModel):
    name: str
    scores: List[int]
    is_valid: bool = True


def test_schema_instantiation():
    # Test Evidence creation
    ev = Evidence(
        content="Benchmark shows 40% performance gain",
        source_type=ProvenanceType.DOCUMENT_DERIVED,
        reliability=0.9,
    )
    assert ev.evidence_id.startswith("E-")
    assert ev.reliability == 0.9
    assert ev.source_type == ProvenanceType.DOCUMENT_DERIVED

    # Test Claim creation
    claim = Claim(
        statement="Solution X is 40% faster",
        status=ClaimSupportStatus.SUPPORTED,
        supporting_evidence_ids=[ev.evidence_id],
    )
    assert claim.claim_id.startswith("C-")
    assert claim.supporting_evidence_ids == [ev.evidence_id]

    # Test DecisionCase creation
    case = DecisionCase(
        title="Migrate to Solution X",
        problem="Legacy system is slow",
        proposed_decision="Adopt Solution X",
        claims=[claim],
        evidence=[ev],
    )
    assert case.case_id.startswith("CASE-")
    assert len(case.claims) == 1
    assert len(case.evidence) == 1


def test_verdict_schema_separation_of_correctness_and_justification():
    # Test Module 53 / 25
    verdict = Verdict(
        case_id="CASE-123",
        verdict=VerdictStatus.PARTIALLY_VALID,
        confidence=0.75,
        decision_correctness=DecisionCorrectness(
            status=DecisionCorrectnessStatus.LIKELY_VALID,
            confidence=0.8,
            summary="Choice appears sound."
        ),
        decision_justification=DecisionJustification(
            status=DecisionJustificationStatus.PARTIAL,
            confidence=0.6,
            summary="Cost claims missing verified receipts."
        ),
        summary_verdict_rationale="Evidence supports speed but not financial forecast."
    )
    assert verdict.verdict == VerdictStatus.PARTIALLY_VALID
    assert verdict.decision_correctness.status == DecisionCorrectnessStatus.LIKELY_VALID
    assert verdict.decision_justification.status == DecisionJustificationStatus.PARTIAL


def test_json_extraction_and_repair():
    raw_markdown = """Here is the extracted information:
    ```json
    {
        'name': 'Decision Test',
        'scores': [10, 20, 30,],
        'is_valid': True,
    }
    ```
    Thank you."""
    
    parsed = parse_and_validate_json(raw_markdown, SampleSchema)
    assert parsed.name == "Decision Test"
    assert parsed.scores == [10, 20, 30]
    assert parsed.is_valid is True


@pytest.mark.asyncio
async def test_mock_llm_provider_and_structured_pipeline():
    provider = get_llm_provider("mock")
    messages = [
        LLMMessage(role="system", content="You are the Case Decomposer."),
        LLMMessage(role="user", content="Please decompose this decision case."),
    ]
    
    class DecomposeResult(BaseModel):
        title: str
        problem: str
        claims: List[dict]
        assumptions: List[dict]
        requirements: List[str]

    result = await execute_structured_prompt(
        provider=provider,
        messages=messages,
        schema=DecomposeResult,
    )
    assert len(result.claims) >= 1
    assert len(result.assumptions) >= 1
    assert len(result.requirements) >= 1
