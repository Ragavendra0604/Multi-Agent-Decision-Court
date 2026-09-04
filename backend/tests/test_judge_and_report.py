"""
Tests for Judge Agent, Verdict Model, Sensitivity Engine & Final Report (Modules 23, 24, 25, 26, 53).
"""

import pytest
from app.schemas.enums import (
    ProvenanceType,
    VerdictStatus,
    DecisionCorrectnessStatus,
    DecisionJustificationStatus,
    RequirementStatus,
)
from app.schemas.entities import (
    DecisionCase,
    Claim,
    Evidence,
    Assumption,
    Requirement,
    AgentFinding,
)
from app.schemas.court import (
    Argument,
    CrossExaminationTurn,
    ReconciledEvidenceItem,
)
from app.services.llm_provider import MockLLMProvider
from app.agents.judge import JudgeAgent
from app.agents.sensitivity_engine import SensitivityEngine
from app.services.report_generator import ReportGenerator


@pytest.fixture
def trial_context():
    case = DecisionCase(
        case_id="CASE-JUDGE-01",
        title="Database Migration to Solution X",
        problem="High database latency impacting customer checkouts",
        proposed_decision="Migrate fully to Solution X",
        claims=[
            Claim(claim_id="C-01", statement="Solution X provides 40% latency drop", is_core_decision_claim=True),
            Claim(claim_id="C-02", statement="Solution X reduces monthly operational costs", is_core_decision_claim=True),
        ],
        evidence=[
            Evidence(evidence_id="E-01", content="Benchmark shows 40% speedup", source_type=ProvenanceType.DOCUMENT_DERIVED),
            Evidence(evidence_id="E-02", content="Pricing sheet shows higher egress charges", source_type=ProvenanceType.SOURCE_VERIFIED),
        ],
        assumptions=[
            Assumption(assumption_id="A-01", statement="Zero retraining needed for engineers", criticality=0.8),
        ],
        requirements=[
            Requirement(req_id="R-01", description="Keep total migration budget under $100k", is_critical=True, is_constraint=True, status=RequirementStatus.SATISFIED),
        ],
    )

    findings = [
        AgentFinding(case_id="CASE-JUDGE-01", task_id="T1", agent="evidence_investigator", target_id="C-01", status="SUPPORTED", reason="Benchmark validates latency", confidence=0.9),
        AgentFinding(case_id="CASE-JUDGE-01", task_id="T2", agent="assumption_auditor", target_id="A-01", status="QUESTIONABLE", reason="Proprietary query language", confidence=0.5),
    ]

    pros_args = [
        Argument(side="PROSECUTION", title="Egress Cost Risk", statement="API egress charges will exceed budget", confidence=0.85, severity_or_strength=0.8)
    ]

    def_args = [
        Argument(side="DEFENSE", title="Throughput Gain", statement="3x higher throughput verified", confidence=0.9, severity_or_strength=0.85)
    ]

    cross_turns = [
        CrossExaminationTurn(
            round_number=1,
            target_claim_id="C-01",
            challenge="Synthetic test doesn't reflect cross-region packet loss",
            defense_response="25% safety margin was added to throughput model",
            resolution_state="PARTIALLY_RESOLVED",
        )
    ]

    reconciled = [
        ReconciledEvidenceItem(
            topic_or_claim_id="C-02",
            conflicting_evidence_ids=["E-01", "E-02"],
            status="PARTIALLY_RESOLVED",
            resolution_rationale="Pricing document overrides initial cost claims.",
        )
    ]

    return case, findings, pros_args, def_args, cross_turns, reconciled


@pytest.mark.asyncio
async def test_judge_agent_adjudication(trial_context):
    case, findings, pros_args, def_args, cross_turns, reconciled = trial_context
    provider = MockLLMProvider("mock")
    judge = JudgeAgent(provider)

    verdict, judge_findings = await judge.adjudicate(
        case=case,
        findings=findings,
        prosecution_arguments=pros_args,
        defense_arguments=def_args,
        cross_examinations=cross_turns,
        reconciliations=reconciled,
    )

    assert verdict.verdict in (VerdictStatus.PARTIALLY_VALID, VerdictStatus.VALID)
    assert verdict.decision_correctness.status in (DecisionCorrectnessStatus.LIKELY_VALID, DecisionCorrectnessStatus.UNCERTAIN)
    assert verdict.decision_justification.status in (DecisionJustificationStatus.PARTIAL, DecisionJustificationStatus.INSUFFICIENT)
    assert len(judge_findings) == 1
    assert judge_findings[0].agent == "judge"


@pytest.mark.asyncio
async def test_sensitivity_engine_and_report_generation(trial_context):
    case, findings, pros_args, def_args, cross_turns, reconciled = trial_context
    provider = MockLLMProvider("mock")
    judge = JudgeAgent(provider)
    sensitivity_engine = SensitivityEngine(provider)

    verdict, _ = await judge.adjudicate(
        case=case,
        findings=findings,
        prosecution_arguments=pros_args,
        defense_arguments=def_args,
        cross_examinations=cross_turns,
        reconciliations=reconciled,
    )

    sensitivity_output, sens_findings = await sensitivity_engine.run_sensitivity_analysis(case, verdict)
    assert len(sensitivity_output.scenarios) >= 1
    assert len(sens_findings) == 1

    report = ReportGenerator.generate_report(
        case=case,
        verdict=verdict,
        cross_examinations=cross_turns,
        reconciliations=reconciled,
        sensitivity=sensitivity_output,
    )

    assert report.report_id.startswith("REP-")
    assert "Multi-Agent Decision Court — Final Verdict Report" in report.markdown_content
    assert verdict.verdict.value in report.markdown_content
    assert "Executive Verdict" in report.markdown_content
    assert "Sensitivity & Tipping-Point Analysis" in report.markdown_content
