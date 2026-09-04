"""
Final Decision Report Generator.
Implements Module 26 (Final Decision Report Generator).
Renders a comprehensive, auditable markdown document containing executive summary,
graph breakdown, adversarial transcripts, sensitivity results, and actionable recommendations.
"""

from datetime import datetime, timezone
from typing import List, Optional

from app.schemas.entities import DecisionCase, generate_id
from app.schemas.court import (
    Verdict,
    FinalDecisionReport,
    CrossExaminationTurn,
    ReconciledEvidenceItem,
)
from app.agents.sensitivity_engine import SensitivityAnalysisOutput


class ReportGenerator:
    """
    Renders structured case verdicts into comprehensive human-readable reports.
    """

    @staticmethod
    def generate_report(
        case: DecisionCase,
        verdict: Verdict,
        cross_examinations: Optional[List[CrossExaminationTurn]] = None,
        reconciliations: Optional[List[ReconciledEvidenceItem]] = None,
        sensitivity: Optional[SensitivityAnalysisOutput] = None,
    ) -> FinalDecisionReport:
        cross_turns = cross_examinations or []
        reconciled_items = reconciliations or []

        # Build Markdown sections
        lines: List[str] = []
        lines.append(f"# Multi-Agent Decision Court — Final Verdict Report")
        lines.append(f"**Case Title:** {case.title}  ")
        lines.append(f"**Case ID:** `{case.case_id}` | **Version:** {case.version} | **Adjudication Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n")
        lines.append("---")

        # 1. Executive Summary & Verdict Callout
        lines.append("## 1. Executive Verdict & Judicial Calibration")
        lines.append(f"> ### **VERDICT:** `{verdict.verdict.value}` (Confidence: {verdict.confidence * 100:.1f}%)")
        lines.append(f"> **Decision Correctness:** `{verdict.decision_correctness.status.value}` (Confidence: {verdict.decision_correctness.confidence * 100:.1f}%)  ")
        lines.append(f"> {verdict.decision_correctness.summary or 'Outcome alignment verified.'}\n>")
        lines.append(f"> **Decision Justification:** `{verdict.decision_justification.status.value}` (Confidence: {verdict.decision_justification.confidence * 100:.1f}%)  ")
        lines.append(f"> {verdict.decision_justification.summary or 'Evidence and logical coherence audited.'}\n")
        lines.append(f"**Judicial Rationale:** {verdict.summary_verdict_rationale}\n")

        # 2. Case Understanding & Decision Statement
        lines.append("## 2. Case Understanding & Proposed Action")
        lines.append(f"- **Problem Statement:** {case.problem}")
        lines.append(f"- **Proposed Decision:** **{case.proposed_decision}**")
        if case.context:
            lines.append(f"- **Context:** {case.context}")
        lines.append("")

        # 3. Requirements & Constraints Fit
        lines.append("## 3. Requirements & Constraints Audit")
        all_reqs = case.requirements + case.constraints
        if all_reqs:
            lines.append("| ID | Description | Type | Status | Satisfaction Score |")
            lines.append("|---|---|---|---|---|")
            for r in all_reqs:
                req_type = "Critical Constraint" if r.is_constraint or r.is_critical else "Requirement"
                lines.append(f"| `{r.req_id}` | {r.description} | {req_type} | `{r.status.value}` | {r.satisfaction_score * 100:.0f}% |")
            lines.append("")
        else:
            lines.append("_No explicit constraints were recorded for this case._\n")

        # 4. Atomic Claims & Evidence Grounding
        lines.append("## 4. Claims Investigation & Evidence Provenance")
        if case.claims:
            for c in case.claims:
                lines.append(f"### Claim `{c.claim_id}`: *\"{c.statement}\"*")
                lines.append(f"- **Support Status:** `{c.status.value}` (Confidence: {c.confidence * 100:.0f}%)")
                if c.supporting_evidence_ids:
                    lines.append(f"- **Supporting Evidence IDs:** `{', '.join(c.supporting_evidence_ids)}`")
                if c.contradicting_evidence_ids:
                    lines.append(f"- **Contradicting Evidence IDs:** `{', '.join(c.contradicting_evidence_ids)}`")
                lines.append("")
        if case.evidence:
            lines.append("**Evidence Catalog:**")
            for e in case.evidence:
                lines.append(f"- `[{e.evidence_id}]` **({e.source_type.value} | Reliability {e.reliability * 100:.0f}%):** {e.content} *(Ref: {e.source_reference or 'N/A'})*")
            lines.append("")

        # 5. Assumption Audit & Dependency Mapping
        lines.append("## 5. Assumption Audit")
        if case.assumptions:
            lines.append("| ID | Assumption Statement | Explicit? | Validity Status | Criticality |")
            lines.append("|---|---|---|---|---|")
            for a in case.assumptions:
                lines.append(f"| `{a.assumption_id}` | {a.statement} | {'Yes' if a.is_explicit else 'No (Hidden)'} | `{a.status.value}` | {a.criticality * 100:.0f}% |")
            lines.append("")

        # 6. Adversarial Summary (Prosecution vs Defense)
        lines.append("## 6. Adversarial Proceedings & Cross-Examination")
        lines.append("### Prosecution Challenges")
        for arg in verdict.counterarguments:
            lines.append(f"- **{arg.title}** (Severity {arg.severity_or_strength * 100:.0f}%): {arg.statement}")
        lines.append("\n### Defense Case & Concessions")
        for arg in verdict.defense_arguments:
            lines.append(f"- **{arg.title}** (Strength {arg.severity_or_strength * 100:.0f}%): {arg.statement}")
        lines.append("")

        if cross_turns:
            lines.append("### Cross-Examination Exchange Transcript")
            for t in cross_turns:
                lines.append(f"**Round {t.round_number} on `{t.target_claim_id}`** (Status: `{t.resolution_state}`):")
                lines.append(f"- *Prosecution:* {t.challenge}")
                lines.append(f"- *Defense:* {t.defense_response}")
                if t.counter_challenge:
                    lines.append(f"- *Follow-up:* {t.counter_challenge}")
                if t.unresolved_uncertainty:
                    lines.append(f"- *Unresolved Gap:* {t.unresolved_uncertainty}")
                lines.append("")

        # 7. Evidence Reconciliation
        if reconciled_items:
            lines.append("## 7. Evidence Reconciliation")
            for rec in reconciled_items:
                lines.append(f"- **Topic/Claim:** `{rec.topic_or_claim_id}` | Status: `{rec.status.value}`")
                lines.append(f"  - **Rationale:** {rec.resolution_rationale}")
                lines.append(f"  - **Source Authority & Date:** {rec.authority_comparison or 'N/A'}")
            lines.append("")

        # 8. Risks & Alternatives Matrix
        lines.append("## 8. Risks & Viable Alternatives")
        if case.risks:
            lines.append("**Identified Risks:**")
            for rk in case.risks:
                lines.append(f"- `[{rk.risk_id}]` **({rk.category.value} - Severity {rk.severity_score * 100:.0f}%):** {rk.description}")
            lines.append("")
        if case.alternatives:
            lines.append("**Comparative Alternatives:**")
            for alt in case.alternatives:
                lines.append(f"- **{alt.title}** ({alt.category} | Feasibility {alt.estimated_feasibility * 100:.0f}% | Fit {alt.requirement_fit_score * 100:.0f}%): {alt.description}")
            lines.append("")

        # 9. Sensitivity Analysis & Decision Drivers
        lines.append("## 9. Sensitivity & Tipping-Point Analysis")
        if sensitivity:
            lines.append(f"**Overall Decision Robustness:** `{sensitivity.robustness_score * 100:.0f}%`")
            if sensitivity.most_fragile_assumptions:
                lines.append(f"- **Most Fragile Assumptions:** {', '.join(sensitivity.most_fragile_assumptions)}")
            if sensitivity.scenarios:
                lines.append("\n**Stress-Test What-If Scenarios:**")
                for s in sensitivity.scenarios:
                    lines.append(f"- **Scenario:** *{s.condition_tested}* $\\rightarrow$ Impact: `{s.verdict_impact}`")
                    if s.tipping_point_threshold:
                        lines.append(f"  - *Tipping Point:* {s.tipping_point_threshold}")
                    if s.recommended_pivot:
                        lines.append(f"  - *Recommended Pivot:* {s.recommended_pivot}")
            lines.append("")

        # 10. Recommended Next Actions & Human Review
        lines.append("## 10. Recommended Next Actions & Human Review")
        if verdict.recommended_next_actions:
            for idx, action in enumerate(verdict.recommended_next_actions, 1):
                lines.append(f"{idx}. {action}")
            lines.append("")
        if verdict.missing_information:
            lines.append("**Missing Information To Collect:**")
            for info in verdict.missing_information:
                lines.append(f"- {info}")
            lines.append("")

        lines.append("> [!NOTE]")
        lines.append("> **Human-in-the-Loop Notice (Module 36):** The Multi-Agent Decision Court provides evidence-grounded validation advice. Final execution authority rests with the designated Human Reviewer.")

        markdown_body = "\n".join(lines)

        return FinalDecisionReport(
            report_id=generate_id("REP"),
            case_id=case.case_id,
            case_title=case.title,
            executive_summary=verdict.summary_verdict_rationale,
            case_understanding=f"Problem: {case.problem} | Proposed Decision: {case.proposed_decision}",
            original_decision=case.proposed_decision,
            verdict=verdict,
            markdown_content=markdown_body,
        )
