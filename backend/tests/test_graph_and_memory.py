"""
Tests for Module 7 (Decision Graph), Module 31 (Memory), and Module 34 (Incremental Re-evaluation).
"""

import pytest
from app.schemas.enums import (
    ProvenanceType,
    ClaimSupportStatus,
    AssumptionStatus,
    NodeType,
    EdgeType,
    VerdictStatus,
)
from app.schemas.entities import (
    DecisionCase,
    Claim,
    Evidence,
    Assumption,
    Requirement,
    Risk,
    Alternative,
    AgentFinding,
)
from app.schemas.court import Verdict
from app.decision_graph.graph_engine import DecisionGraph
from app.decision_graph.incremental_engine import (
    find_downstream_affected_nodes,
    compute_invalidation_plan,
)
from app.memory.memory_manager import MemoryManager, KnowledgeDocument


def test_decision_graph_build_and_propagation():
    ev1 = Evidence(
        evidence_id="E-01",
        content="Benchmark shows 40% latency reduction",
        source_type=ProvenanceType.DOCUMENT_DERIVED,
        reliability=0.9,
        strength=0.85,
        claims_supported=["C-01"],
    )
    ev2 = Evidence(
        evidence_id="E-02",
        content="Pricing sheet indicates 20% higher cloud egress fee",
        source_type=ProvenanceType.SOURCE_VERIFIED,
        reliability=0.95,
        strength=0.8,
        claims_contradicted=["C-02"],
    )
    c1 = Claim(
        claim_id="C-01",
        statement="Solution X is faster",
        status=ClaimSupportStatus.SUPPORTED,
        confidence=0.85,
    )
    c2 = Claim(
        claim_id="C-02",
        statement="Solution X is cheaper",
        status=ClaimSupportStatus.CONTRADICTED,
        confidence=0.4,
    )
    a1 = Assumption(
        assumption_id="A-01",
        statement="Network bandwidth remains unthrottled",
        dependent_claim_ids=["C-01"],
        criticality=0.7,
    )
    req = Requirement(
        req_id="R-01",
        description="Must achieve lower operating costs",
        is_critical=True,
        satisfaction_score=0.3,
    )
    case = DecisionCase(
        case_id="CASE-999",
        title="Solution X Adoption",
        problem="Current system is too slow and costly",
        proposed_decision="Migrate fully to Solution X",
        claims=[c1, c2],
        evidence=[ev1, ev2],
        assumptions=[a1],
        requirements=[req],
    )

    graph = DecisionGraph.from_case(case)
    
    # Verify nodes
    node_ids = [n.id for n in graph.get_nodes()]
    assert "CASE-999" in node_ids
    assert "C-01" in node_ids
    assert "E-01" in node_ids
    assert "A-01" in node_ids
    assert "R-01" in node_ids

    # Verify incoming support for C-01
    support_score, supporting_nodes = graph.get_incoming_support("C-01")
    assert support_score > 0
    assert "E-01" in supporting_nodes

    # Verify incoming contradiction for C-02
    contra_score, contra_nodes = graph.get_incoming_contradictions("C-02")
    assert contra_score > 0
    assert "E-02" in contra_nodes

    # Verify subgraph extraction
    subgraph = graph.get_subgraph_for_node("C-01", depth=1)
    sub_node_ids = [n.id for n in subgraph.get_nodes()]
    assert "C-01" in sub_node_ids
    assert "E-01" in sub_node_ids


def test_incremental_invalidation():
    ev = Evidence(evidence_id="E-01", content="Speed test", claims_supported=["C-01"])
    c = Claim(claim_id="C-01", statement="System is fast", confidence=0.8)
    req = Requirement(req_id="R-01", description="Fast speed", satisfaction_score=0.9)
    case = DecisionCase(
        case_id="CASE-100",
        problem="Slow speed",
        proposed_decision="Upgrade",
        claims=[c],
        evidence=[ev],
        requirements=[req],
    )
    graph = DecisionGraph.from_case(case)

    # When evidence E-01 changes, downstream affected nodes must include C-01 and DEC-CASE-100
    plan = compute_invalidation_plan(graph, ["E-01"])
    assert "C-01" in plan.affected_node_ids
    assert "DEC-CASE-100" in plan.affected_node_ids
    assert "evidence_investigator" in plan.affected_agent_types
    assert "judge" in plan.affected_agent_types


def test_memory_isolation_and_operations():
    mem = MemoryManager()
    finding = AgentFinding(
        case_id="CASE-01",
        task_id="TASK-01",
        agent="evidence_investigator",
        target_id="C-01",
        status="SUPPORTED",
        reason="Verified against benchmark logs",
        confidence=0.9,
    )
    mem.add_agent_finding("CASE-01", finding, tenant_id="tenant_A")
    
    # Verify tenant A has finding
    case_mem_a = mem.get_or_create_case_memory("CASE-01", tenant_id="tenant_A")
    assert len(case_mem_a.findings) == 1
    assert case_mem_a.findings[0].agent == "evidence_investigator"

    # Verify tenant B is isolated
    case_mem_b = mem.get_or_create_case_memory("CASE-01", tenant_id="tenant_B")
    assert len(case_mem_b.findings) == 0

    # Test Knowledge search
    mem.add_knowledge_doc(KnowledgeDocument(
        doc_id="DOC-1",
        title="Company Cloud Security Standard",
        category="Policy",
        content="All database migrations must maintain SOC2 Type II compliance.",
        tags=["security", "compliance", "migration"],
        tenant_id="tenant_A"
    ))
    search_results = mem.search_knowledge("SOC2 security compliance", tenant_id="tenant_A")
    assert len(search_results) == 1
    assert search_results[0].doc_id == "DOC-1"
