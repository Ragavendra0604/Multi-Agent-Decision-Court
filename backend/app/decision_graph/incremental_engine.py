"""
Incremental Re-evaluation Engine.
Implements Module 34 (Incremental Re-evaluation) and Module 35 (Versioning).
Identifies downstream impacted nodes when evidence/assumptions change to avoid redundant agent executions.
"""

from typing import Any, Dict, List, Set
import networkx as nx

from app.schemas.enums import NodeType
from app.decision_graph.graph_engine import DecisionGraph


class InvalidationPlan:
    def __init__(
        self,
        changed_node_ids: List[str],
        affected_node_ids: List[str],
        affected_agent_types: List[str],
    ):
        self.changed_node_ids = changed_node_ids
        self.affected_node_ids = affected_node_ids
        self.affected_agent_types = affected_agent_types

    def to_dict(self) -> Dict[str, Any]:
        return {
            "changed_node_ids": self.changed_node_ids,
            "affected_node_ids": self.affected_node_ids,
            "affected_agent_types": self.affected_agent_types,
        }


def find_downstream_affected_nodes(graph: DecisionGraph, changed_node_ids: List[str]) -> Set[str]:
    """
    Finds all nodes downstream from the changed nodes in the directed decision graph.
    """
    g = graph._graph
    affected = set(changed_node_ids)
    
    for start_node in changed_node_ids:
        if g.has_node(start_node):
            # Outgoing reachability in directed graph
            descendants = nx.descendants(g, start_node)
            affected.update(descendants)
            
    return affected


def compute_invalidation_plan(graph: DecisionGraph, changed_node_ids: List[str]) -> InvalidationPlan:
    """
    Computes which agents must re-run based on the node types affected.
    Module 34 & Module 46 (Cost Optimization: never rerun unaffected tasks).
    """
    affected_nodes = find_downstream_affected_nodes(graph, changed_node_ids)
    affected_agents: Set[str] = set()

    for node_id in affected_nodes:
        node = graph.get_node(node_id)
        if not node:
            continue
            
        if node.node_type == NodeType.CLAIM:
            affected_agents.add("evidence_investigator")
            affected_agents.add("logic_analyst")
        elif node.node_type == NodeType.ASSUMPTION:
            affected_agents.add("assumption_auditor")
        elif node.node_type in (NodeType.REQUIREMENT, NodeType.CONSTRAINT):
            affected_agents.add("requirement_validator")
        elif node.node_type == NodeType.THEORY:
            affected_agents.add("theory_analyst")
        elif node.node_type == NodeType.RISK:
            affected_agents.add("risk_analyst")
        elif node.node_type == NodeType.ALTERNATIVE:
            affected_agents.add("alternative_generator")

    # If any substantive analytical node changed, adversarial and judge layers must re-evaluate
    if affected_agents:
        affected_agents.add("prosecution")
        affected_agents.add("defense")
        affected_agents.add("cross_examiner")
        affected_agents.add("reconciliation")
        affected_agents.add("judge")

    return InvalidationPlan(
        changed_node_ids=changed_node_ids,
        affected_node_ids=list(affected_nodes),
        affected_agent_types=list(affected_agents),
    )
