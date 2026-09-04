"""
Decision Graph Engine.
Implements Module 7 (Decision Graph Engine), Module 46 (Subgraph Filtering for Cost Optimization),
and graph serialization for React Flow visualization.
"""

from typing import Any, Dict, List, Optional, Set, Tuple
import networkx as nx

from app.schemas.enums import NodeType, EdgeType
from app.schemas.entities import (
    DecisionGraphNode,
    DecisionGraphEdge,
    DecisionGraphData,
    DecisionCase,
    Claim,
    Evidence,
    Assumption,
    Requirement,
    Theory,
    Risk,
    Alternative,
)


class DecisionGraph:
    """
    Central reasoning representation using a directed graph.
    Nodes represent decision artifacts (Case, Problem, Claim, Evidence, Assumption, etc.).
    Edges represent semantic justification relationships (SUPPORTS, CONTRADICTS, ASSUMES, etc.).
    """

    def __init__(self, case_id: Optional[str] = None):
        self.case_id = case_id or "default"
        self._graph = nx.DiGraph()

    def add_node(
        self,
        node_id: str,
        label: str,
        node_type: NodeType,
        properties: Optional[Dict[str, Any]] = None,
        confidence: float = 1.0,
    ) -> DecisionGraphNode:
        props = properties or {}
        self._graph.add_node(
            node_id,
            label=label,
            node_type=node_type,
            properties=props,
            confidence=confidence,
        )
        return DecisionGraphNode(
            id=node_id,
            label=label,
            node_type=node_type,
            properties=props,
            confidence=confidence,
        )

    def add_edge(
        self,
        source: str,
        target: str,
        relation: EdgeType,
        weight: float = 1.0,
        properties: Optional[Dict[str, Any]] = None,
    ) -> DecisionGraphEdge:
        props = properties or {}
        self._graph.add_edge(
            source,
            target,
            relation=relation,
            weight=weight,
            properties=props,
        )
        return DecisionGraphEdge(
            source=source,
            target=target,
            relation=relation,
            weight=weight,
            properties=props,
        )

    def get_node(self, node_id: str) -> Optional[DecisionGraphNode]:
        if not self._graph.has_node(node_id):
            return None
        data = self._graph.nodes[node_id]
        return DecisionGraphNode(
            id=node_id,
            label=data.get("label", node_id),
            node_type=data.get("node_type", NodeType.CLAIM),
            properties=data.get("properties", {}),
            confidence=data.get("confidence", 1.0),
        )

    def get_nodes(self) -> List[DecisionGraphNode]:
        nodes = []
        for node_id, data in self._graph.nodes(data=True):
            nodes.append(
                DecisionGraphNode(
                    id=node_id,
                    label=data.get("label", node_id),
                    node_type=data.get("node_type", NodeType.CLAIM),
                    properties=data.get("properties", {}),
                    confidence=data.get("confidence", 1.0),
                )
            )
        return nodes

    def get_edges(self) -> List[DecisionGraphEdge]:
        edges = []
        for u, v, data in self._graph.edges(data=True):
            edges.append(
                DecisionGraphEdge(
                    source=u,
                    target=v,
                    relation=data.get("relation", EdgeType.SUPPORTS),
                    weight=data.get("weight", 1.0),
                    properties=data.get("properties", {}),
                )
            )
        return edges

    def to_data(self) -> DecisionGraphData:
        """
        Converts the graph to a serializable model compatible with React Flow.
        """
        return DecisionGraphData(nodes=self.get_nodes(), edges=self.get_edges())

    @classmethod
    def from_case(cls, case: DecisionCase) -> "DecisionGraph":
        """
        Builds a comprehensive decision graph from a DecisionCase object.
        """
        dg = cls(case_id=case.case_id)
        
        # 1. Root Case & Decision Nodes
        dg.add_node(case.case_id, case.title, NodeType.CASE, {"problem": case.problem})
        dec_id = f"DEC-{case.case_id}"
        dg.add_node(dec_id, case.proposed_decision, NodeType.DECISION)
        dg.add_edge(dec_id, case.case_id, EdgeType.DERIVED_FROM)

        # 2. Problem
        prob_id = f"PROB-{case.case_id}"
        dg.add_node(prob_id, case.problem, NodeType.PROBLEM)
        dg.add_edge(case.case_id, prob_id, EdgeType.CAUSED_BY)

        # 3. Requirements & Constraints
        for r in case.requirements:
            dg.add_node(r.req_id, r.description, NodeType.REQUIREMENT, {"is_critical": r.is_critical, "score": r.satisfaction_score})
            dg.add_edge(dec_id, r.req_id, EdgeType.SATISFIES if r.satisfaction_score >= 0.5 else EdgeType.VIOLATES)

        for c in case.constraints:
            dg.add_node(c.req_id, c.description, NodeType.CONSTRAINT, {"is_critical": True})
            dg.add_edge(dec_id, c.req_id, EdgeType.SATISFIES if c.satisfaction_score >= 0.5 else EdgeType.VIOLATES)

        # 4. Claims
        for clm in case.claims:
            dg.add_node(clm.claim_id, clm.statement, NodeType.CLAIM, {"status": clm.status.value, "confidence": clm.confidence})
            dg.add_edge(clm.claim_id, dec_id, EdgeType.SUPPORTS, weight=clm.confidence)

        # 5. Evidence
        for ev in case.evidence:
            dg.add_node(
                ev.evidence_id,
                ev.content[:80] + ("..." if len(ev.content) > 80 else ""),
                NodeType.EVIDENCE,
                {"source_type": ev.source_type.value, "reliability": ev.reliability, "strength": ev.strength},
                confidence=ev.reliability,
            )
            for c_id in ev.claims_supported:
                if dg.get_node(c_id):
                    dg.add_edge(ev.evidence_id, c_id, EdgeType.SUPPORTS, weight=ev.strength)
            for c_id in ev.claims_contradicted:
                if dg.get_node(c_id):
                    dg.add_edge(ev.evidence_id, c_id, EdgeType.CONTRADICTS, weight=ev.strength)

        # 6. Assumptions
        for a in case.assumptions:
            dg.add_node(
                a.assumption_id,
                a.statement,
                NodeType.ASSUMPTION,
                {"status": a.status.value, "validity_score": a.validity_score, "criticality": a.criticality},
            )
            for c_id in a.dependent_claim_ids:
                if dg.get_node(c_id):
                    dg.add_edge(a.assumption_id, c_id, EdgeType.ASSUMES, weight=a.criticality)

        # 7. Risks
        for rk in case.risks:
            dg.add_node(rk.risk_id, rk.description, NodeType.RISK, {"category": rk.category.value, "severity": rk.severity_score})
            for c_id in rk.affected_claim_ids:
                if dg.get_node(c_id):
                    dg.add_edge(rk.risk_id, c_id, EdgeType.REFUTES, weight=rk.severity_score)

        # 8. Alternatives
        for alt in case.alternatives:
            dg.add_node(alt.alt_id, alt.title, NodeType.ALTERNATIVE, {"feasibility": alt.estimated_feasibility})
            dg.add_edge(alt.alt_id, dec_id, EdgeType.ALTERNATIVE_TO)

        return dg

    def get_subgraph_for_node(self, node_id: str, depth: int = 2) -> "DecisionGraph":
        """
        Extracts a localized subgraph around a node to pass concise context to specialized agents (Module 46).
        """
        if not self._graph.has_node(node_id):
            return DecisionGraph(self.case_id)
        
        # Get undirected neighborhood up to depth
        undirected = self._graph.to_undirected()
        reachable = nx.single_source_shortest_path_length(undirected, node_id, cutoff=depth).keys()
        
        sub = self._graph.subgraph(reachable).copy()
        new_dg = DecisionGraph(self.case_id)
        new_dg._graph = sub
        return new_dg

    def get_incoming_support(self, target_node_id: str) -> Tuple[float, List[str]]:
        """
        Calculates cumulative incoming support and lists supporting node IDs.
        """
        if not self._graph.has_node(target_node_id):
            return 0.0, []
        
        supporting_nodes = []
        total_support = 0.0
        
        for u, v, data in self._graph.in_edges(target_node_id, data=True):
            if data.get("relation") == EdgeType.SUPPORTS:
                supporting_nodes.append(u)
                weight = data.get("weight", 1.0)
                node_conf = self._graph.nodes[u].get("confidence", 1.0)
                total_support += weight * node_conf

        return total_support, supporting_nodes

    def get_incoming_contradictions(self, target_node_id: str) -> Tuple[float, List[str]]:
        """
        Calculates cumulative incoming contradictions and lists refuting node IDs.
        """
        if not self._graph.has_node(target_node_id):
            return 0.0, []
        
        contradicting_nodes = []
        total_contradiction = 0.0
        
        for u, v, data in self._graph.in_edges(target_node_id, data=True):
            if data.get("relation") in (EdgeType.CONTRADICTS, EdgeType.REFUTES, EdgeType.VIOLATES):
                contradicting_nodes.append(u)
                weight = data.get("weight", 1.0)
                node_conf = self._graph.nodes[u].get("confidence", 1.0)
                total_contradiction += weight * node_conf

        return total_contradiction, contradicting_nodes
