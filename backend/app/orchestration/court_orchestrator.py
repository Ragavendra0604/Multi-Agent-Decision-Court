"""
Court Orchestrator & Multi-Agent Execution Control Plane.
Implements Module 8 (Court Orchestrator), Module 33 (Task Graph & Parallel Execution),
and Module 47 (Reliability & Timeouts).
"""

import asyncio
from datetime import datetime, timezone
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from app.config import settings
from app.schemas.enums import CaseState, VerdictStatus, ProvenanceType
from app.schemas.entities import DecisionCase, AgentFinding, generate_id
from app.schemas.court import (
    Verdict,
    FinalDecisionReport,
    Argument,
    CrossExaminationTurn,
    ReconciledEvidenceItem,
)
from app.decision_graph.graph_engine import DecisionGraph
from app.memory.memory_manager import memory_manager
from app.services.llm_provider import BaseLLMProvider, get_llm_provider
from app.services.report_generator import ReportGenerator

# Import all specialized agents
from app.agents.case_analyst import CaseAnalystAgent
from app.agents.evidence_investigator import EvidenceInvestigatorAgent
from app.agents.assumption_auditor import AssumptionAuditorAgent
from app.agents.logic_analyst import LogicAnalystAgent
from app.agents.requirement_validator import RequirementValidatorAgent
from app.agents.theory_analyst import TheoryAnalystAgent
from app.agents.risk_analyst import RiskAnalystAgent
from app.agents.alternative_generator import AlternativeGeneratorAgent
from app.agents.prosecution import ProsecutionAgent
from app.agents.defense import DefenseAgent
from app.agents.cross_examiner import CrossExaminationEngine
from app.evidence.reconciliation import EvidenceReconciliationEngine
from app.agents.judge import JudgeAgent
from app.agents.sensitivity_engine import SensitivityEngine

logger = logging.getLogger(__name__)


class CourtEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: generate_id("EVT"))
    case_id: str
    phase: str
    message: str
    agent: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CourtExecutionResult(BaseModel):
    case_id: str
    state: CaseState
    verdict: Verdict
    report: FinalDecisionReport
    graph_data: Dict[str, Any]
    findings: List[AgentFinding]
    events: List[CourtEvent]
    duration_seconds: float


class CourtOrchestrator:
    """
    Central control plane coordinating the multi-agent decision court pipeline.
    Executes independent analytical agents in parallel, conducts adversarial cross-examination,
    reconciles evidence, summons the Judge, runs sensitivity tests, and outputs the final report.
    """

    def __init__(
        self,
        provider: Optional[BaseLLMProvider] = None,
        event_callback: Optional[Callable[[CourtEvent], None]] = None,
    ):
        self.provider = provider or get_llm_provider()
        self.event_callback = event_callback

    def _emit_event(self, case_id: str, phase: str, message: str, agent: Optional[str] = None, data: Optional[Dict[str, Any]] = None) -> CourtEvent:
        event = CourtEvent(
            case_id=case_id,
            phase=phase,
            message=message,
            agent=agent,
            data=data or {},
        )
        if self.event_callback:
            try:
                self.event_callback(event)
            except Exception as e:
                logger.warning(f"Event callback failed: {e}")
        return event

    async def execute_court_session(self, case: DecisionCase) -> CourtExecutionResult:
        start_time = datetime.now(timezone.utc)
        events: List[CourtEvent] = []
        all_findings: List[AgentFinding] = []

        case_id = case.case_id
        events.append(self._emit_event(case_id, "SUBMITTED", f"Case '{case.title}' submitted to Court."))

        # ---------------------------------------------------------------------
        # Phase 1: Case Analysis & Scope Framing (Module 9 & 10)
        # ---------------------------------------------------------------------
        events.append(self._emit_event(case_id, "ANALYZING", "Case Analyst examining objective, scope, and claims.", agent="case_analyst"))
        case_analyst = CaseAnalystAgent(self.provider)
        analysis_out, ca_findings = await case_analyst.analyze(case)
        all_findings.extend(ca_findings)
        for f in ca_findings:
            memory_manager.add_agent_finding(case_id, f)

        # Build initial Decision Graph
        graph = DecisionGraph.from_case(case)

        # ---------------------------------------------------------------------
        # Phase 2: Parallel Analytical Agents Execution (Module 33)
        # ---------------------------------------------------------------------
        events.append(self._emit_event(
            case_id,
            "INVESTIGATING",
            "Dispatching 7 analytical agents concurrently (Evidence, Logic, Requirements, Assumptions, Theories, Risks, Alternatives).",
        ))

        evidence_agent = EvidenceInvestigatorAgent(self.provider)
        assumption_agent = AssumptionAuditorAgent(self.provider)
        logic_agent = LogicAnalystAgent(self.provider)
        requirement_agent = RequirementValidatorAgent(self.provider)
        theory_agent = TheoryAnalystAgent(self.provider)
        risk_agent = RiskAnalystAgent(self.provider)
        alternative_agent = AlternativeGeneratorAgent(self.provider)

        # Execute in parallel via asyncio.gather with timeout protection
        async def run_safe(coro, agent_name: str):
            try:
                return await asyncio.wait_for(coro, timeout=settings.LLM_TIMEOUT_SECONDS)
            except Exception as e:
                logger.error(f"Agent {agent_name} failed: {e}")
                return None, [
                    AgentFinding(
                        case_id=case_id,
                        task_id=generate_id(f"TASK-ERR-{agent_name}"),
                        agent=agent_name,
                        target_id=case.proposed_decision,
                        status="ERROR",
                        reason=f"Agent timed out or failed: {str(e)}",
                        confidence=0.0,
                    )
                ]

        results = await asyncio.gather(
            run_safe(evidence_agent.investigate_claims(case), "evidence_investigator"),
            run_safe(assumption_agent.audit_assumptions(case), "assumption_auditor"),
            run_safe(logic_agent.analyze_logic(case), "logic_analyst"),
            run_safe(requirement_agent.validate_requirements(case), "requirement_validator"),
            run_safe(theory_agent.analyze_theories(case), "theory_analyst"),
            run_safe(risk_agent.analyze_risks(case), "risk_analyst"),
            run_safe(alternative_agent.generate_alternatives(case), "alternative_generator"),
        )

        (
            (ev_investigations, ev_findings),
            (assump_out, assump_findings),
            (logic_out, logic_findings),
            (req_out, req_findings),
            (theory_out, theory_findings),
            (risk_out, risk_findings),
            (alt_out, alt_findings),
        ) = results

        for f_list in (ev_findings, assump_findings, logic_findings, req_findings, theory_findings, risk_findings, alt_findings):
            all_findings.extend(f_list)
            for f in f_list:
                memory_manager.add_agent_finding(case_id, f)

        # ---------------------------------------------------------------------
        # Phase 3: Adversarial Layer (Prosecution, Defense, Cross-Exam) (Modules 16, 17, 20)
        # ---------------------------------------------------------------------
        events.append(self._emit_event(case_id, "DEBATING", "Commencing Prosecution and Defense adversarial proceedings.", agent="court"))

        prosecution_agent = ProsecutionAgent(self.provider)
        defense_agent = DefenseAgent(self.provider)

        _, pros_args, pros_findings = await prosecution_agent.prosecute_case(case, all_findings)
        all_findings.extend(pros_findings)
        for a in pros_args:
            memory_manager.add_argument(case_id, a)

        _, def_args, def_findings = await defense_agent.defend_case(case, pros_args, all_findings)
        all_findings.extend(def_findings)
        for a in def_args:
            memory_manager.add_argument(case_id, a)

        # Cross-Examination on primary disputed claims
        cross_engine = CrossExaminationEngine(self.provider, max_rounds=settings.MAX_DEBATE_ROUNDS)
        cross_turns: List[CrossExaminationTurn] = []

        if case.claims:
            for target_claim in case.claims[:2]:  # Debate top claims
                c_turns, c_findings = await cross_engine.cross_examine_claim(case, target_claim, pros_args, def_args)
                cross_turns.extend(c_turns)
                all_findings.extend(c_findings)
                for t in c_turns:
                    memory_manager.add_cross_examination(case_id, t)

        # ---------------------------------------------------------------------
        # Phase 4: Evidence Reconciliation (Module 21)
        # ---------------------------------------------------------------------
        events.append(self._emit_event(case_id, "RECONCILING", "Reconciling conflicting evidence and source authority.", agent="reconciliation"))
        reconciliation_engine = EvidenceReconciliationEngine(self.provider)
        reconciled_items, rec_findings = await reconciliation_engine.reconcile_conflicts(case, case.evidence)
        all_findings.extend(rec_findings)

        # ---------------------------------------------------------------------
        # Phase 5: Judicial Adjudication (Modules 24, 25, 53)
        # ---------------------------------------------------------------------
        events.append(self._emit_event(case_id, "JUDGING", "Supreme Judge synthesizing evidence and arguments for verdict.", agent="judge"))
        judge_agent = JudgeAgent(self.provider)
        verdict, judge_findings = await judge_agent.adjudicate(
            case=case,
            findings=all_findings,
            prosecution_arguments=pros_args,
            defense_arguments=def_args,
            cross_examinations=cross_turns,
            reconciliations=reconciled_items,
        )
        all_findings.extend(judge_findings)
        memory_manager.record_verdict(case_id, verdict)

        # ---------------------------------------------------------------------
        # Phase 6: Sensitivity Analysis & Final Decision Report (Modules 23 & 26)
        # ---------------------------------------------------------------------
        events.append(self._emit_event(case_id, "SENSITIVITY", "Running What-If stress testing scenarios.", agent="sensitivity_engine"))
        sensitivity_engine = SensitivityEngine(self.provider)
        sensitivity_output, sens_findings = await sensitivity_engine.run_sensitivity_analysis(case, verdict)
        all_findings.extend(sens_findings)

        events.append(self._emit_event(case_id, "VERDICT_READY", f"Verdict delivered: {verdict.verdict.value}.", agent="judge"))
        final_report = ReportGenerator.generate_report(
            case=case,
            verdict=verdict,
            cross_examinations=cross_turns,
            reconciliations=reconciled_items,
            sensitivity=sensitivity_output,
        )

        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()

        return CourtExecutionResult(
            case_id=case_id,
            state=CaseState.VERDICT_READY,
            verdict=verdict,
            report=final_report,
            graph_data=graph.to_data().model_dump(),
            findings=all_findings,
            events=events,
            duration_seconds=duration,
        )
