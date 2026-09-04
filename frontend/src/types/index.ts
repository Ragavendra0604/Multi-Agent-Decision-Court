export type CaseState =
  | 'DRAFT'
  | 'SUBMITTED'
  | 'ANALYZING'
  | 'INVESTIGATING'
  | 'DEBATING'
  | 'RECONCILING'
  | 'JUDGING'
  | 'VERDICT_READY'
  | 'HUMAN_REVIEW'
  | 'CLOSED';

export type VerdictStatus =
  | 'VALID'
  | 'PARTIALLY_VALID'
  | 'INVALID'
  | 'INSUFFICIENT_EVIDENCE'
  | 'INCONCLUSIVE'
  | 'HIGH_RISK'
  | 'REQUIRES_HUMAN_REVIEW';

export interface EvidenceItem {
  evidence_id: string;
  source_type: string;
  source_reference?: string;
  content: string;
  reliability: number;
  strength: number;
  claims_supported: string[];
  claims_contradicted: string[];
}

export interface ClaimItem {
  claim_id: string;
  statement: string;
  category?: string;
  status: string;
  confidence: number;
  supporting_evidence_ids: string[];
  contradicting_evidence_ids: string[];
  is_core_decision_claim: boolean;
}

export interface AssumptionItem {
  assumption_id: string;
  statement: string;
  is_explicit: boolean;
  status: string;
  criticality: number;
}

export interface RequirementItem {
  req_id: string;
  description: string;
  is_critical: boolean;
  is_constraint: boolean;
  status: string;
  satisfaction_score: number;
}

export interface RiskItem {
  risk_id: string;
  category: string;
  description: string;
  severity_score: number;
}

export interface AlternativeItem {
  alt_id: string;
  title: string;
  category: string;
  description: string;
  estimated_feasibility: number;
  requirement_fit_score: number;
}

export interface DecisionCaseData {
  case_id: string;
  title: string;
  problem: string;
  proposed_decision: string;
  context?: string;
  claims: ClaimItem[];
  evidence: EvidenceItem[];
  assumptions: AssumptionItem[];
  requirements: RequirementItem[];
  constraints: RequirementItem[];
  risks: RiskItem[];
  alternatives: AlternativeItem[];
  version: number;
}

export interface GraphNode {
  id: string;
  label: string;
  node_type: string;
  confidence: number;
  properties: Record<string, any>;
}

export interface GraphEdge {
  source: string;
  target: string;
  relation: string;
  weight: number;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface CaseResponse {
  case_id: string;
  title: string;
  problem: string;
  proposed_decision: string;
  state: CaseState;
  version: number;
  data: DecisionCaseData;
  graph: GraphData;
}

export interface ArgumentItem {
  arg_id: string;
  side: 'PROSECUTION' | 'DEFENSE';
  title: string;
  target_claim_id?: string;
  statement: string;
  severity_or_strength: number;
}

export interface CrossExamTurnItem {
  turn_id: string;
  round_number: number;
  target_claim_id: string;
  challenge: string;
  defense_response: string;
  counter_challenge?: string;
  resolution_state: string;
  unresolved_uncertainty?: string;
}

export interface ReconciledItem {
  reconciliation_id: string;
  topic_or_claim_id: string;
  status: string;
  resolution_rationale: string;
  authority_comparison?: string;
}

export interface VerdictData {
  verdict_id: string;
  case_id: string;
  verdict: VerdictStatus;
  confidence: number;
  decision_correctness: {
    status: string;
    confidence: number;
    summary?: string;
  };
  decision_justification: {
    status: string;
    confidence: number;
    summary?: string;
  };
  summary_verdict_rationale: string;
  critical_decision_drivers: string[];
  unresolved_questions: string[];
  missing_information: string[];
  recommended_next_actions: string[];
  counterarguments: ArgumentItem[];
  defense_arguments: ArgumentItem[];
}

export interface CourtEvent {
  event_id: string;
  case_id: string;
  phase: string;
  message: string;
  agent?: string;
  data: Record<string, any>;
  timestamp: string;
}

export interface WhatIfScenario {
  scenario_id: string;
  scenario_title: string;
  condition_tested: string;
  verdict_impact: string;
  tipping_point_threshold?: string;
  recommended_pivot?: string;
  rationale: string;
}

export interface SensitivityData {
  most_fragile_assumptions: string[];
  critical_cost_or_risk_thresholds: string[];
  scenarios: WhatIfScenario[];
  robustness_score: number;
}
