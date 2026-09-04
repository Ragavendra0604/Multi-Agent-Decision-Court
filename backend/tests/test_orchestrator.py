"""
Tests for Court Orchestrator & Multi-Agent Execution DAG (Modules 8, 33, 47).
"""

import pytest
from app.schemas.enums import (
    ProvenanceType,
    CaseState,
    VerdictStatus,
    ClaimSupportStatus,
)
from app.schemas.entities import (
    DecisionCase,
    Claim,
    Evidence,
    Assumption,
    Requirement,
    Risk,
    Theory,
    Alternative,
)
from app.services.llm_provider import MockLLMProvider
from app.orchestration.court_orchestrator import CourtOrchestrator, CourtEvent


@pytest.fixture
def full_court_case():
    return DecisionCase(
        case_id="CASE-FULL-01",
        title="Migrate Core Database to Solution X",
        problem="Legacy MySQL cluster is suffering 99th percentile latency spikes under peak sales load",
        proposed_decision="Migrate production transactional database to Solution X distributed cluster",
        context="E-commerce store handling 10,000 active checkouts per hour during peak promotions.",
        claims=[
            Claim(claim_id="C-01", statement="Solution X reduces latency by 40%", is_core_decision_claim=True),
            Claim(claim_id="C-02", statement="Solution X provides 99.99% availability with zero manual failover", is_core_decision_claim=True),
        ],
        evidence=[
            Evidence(evidence_id="E-01", content="Staging load test confirms 40% latency reduction at 15,000 RPS", source_type=ProvenanceType.DOCUMENT_DERIVED),
            Evidence(evidence_id="E-02", content="Vendor pricing documentation indicates 20% higher multi-region egress costs", source_type=ProvenanceType.SOURCE_VERIFIED),
        ],
        assumptions=[
            Assumption(assumption_id="A-01", statement="Engineering team can transition schemas without external contractor hire", criticality=0.75),
        ],
        requirements=[
            Requirement(req_id="R-01", description="Keep total migration budget under $100k", is_critical=True, is_constraint=True),
            Requirement(req_id="R-02", description="Maintain zero data loss (RPO = 0)", is_critical=True, is_constraint=True),
        ],
        theories=[
            Theory(theory_id="T-01", name="Distributed Raft consensus guarantees linearizable reads", preconditions=["Low latency network interconnect"]),
        ],
        risks=[
            Risk(risk_id="RISK-01", description="Schema migration rollback complexity", severity_score=0.5),
        ],
        alternatives=[
            Alternative(alt_id="ALT-01", title="Optimize existing MySQL read replicas and add Redis caching", description="Refactor hot query indices"),
        ],
    )


@pytest.mark.asyncio
async def test_court_orchestrator_end_to_end(full_court_case):
    emitted_events = []

    def on_event(event: CourtEvent):
        emitted_events.append(event)

    provider = MockLLMProvider("mock")
    orchestrator = CourtOrchestrator(provider=provider, event_callback=on_event)

    result = await orchestrator.execute_court_session(full_court_case)

    # Verify overall result
    assert result.case_id == "CASE-FULL-01"
    assert result.state == CaseState.VERDICT_READY
    assert result.verdict.verdict in (VerdictStatus.PARTIALLY_VALID, VerdictStatus.VALID)
    assert len(result.findings) >= 10  # Findings from all agents
    assert len(result.events) >= 5
    assert len(emitted_events) >= 5

    # Verify Report
    assert result.report.report_id.startswith("REP-")
    assert "Multi-Agent Decision Court — Final Verdict Report" in result.report.markdown_content

    # Verify Graph data serialized for frontend
    assert "nodes" in result.graph_data
    assert "edges" in result.graph_data
    assert len(result.graph_data["nodes"]) >= 5

    # Verify Event sequence
    event_phases = [e.phase for e in emitted_events]
    assert "SUBMITTED" in event_phases
    assert "ANALYZING" in event_phases
    assert "INVESTIGATING" in event_phases
    assert "DEBATING" in event_phases
    assert "JUDGING" in event_phases
    assert "VERDICT_READY" in event_phases
