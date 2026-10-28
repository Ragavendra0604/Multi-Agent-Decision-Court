"""
Final Decision Report Generator.
Implements Module 26 (Final Decision Report Generator).
Renders a comprehensive, auditable markdown document containing executive summary,
graph breakdown, adversarial transcripts, sensitivity results, and actionable recommendations.
"""

from datetime import datetime, timezone
from typing import List, Optional
import markdown

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

    @classmethod
    def generate_html(
        cls,
        case: DecisionCase,
        verdict: Verdict,
        cross_examinations: Optional[List[CrossExaminationTurn]] = None,
        reconciliations: Optional[List[ReconciledEvidenceItem]] = None,
        sensitivity: Optional[SensitivityAnalysisOutput] = None,
    ) -> str:
        """
        Generates a self-contained, publication-grade executive HTML decision dossier
        with integrated print styling for instantaneous PDF export.
        """
        report = cls.generate_report(case, verdict, cross_examinations, reconciliations, sensitivity)
        html_body = markdown.markdown(
            report.markdown_content,
            extensions=["tables", "fenced_code", "nl2br", "sane_lists"]
        )

        html_body = html_body.replace(
            "<blockquote>\n<p>[!NOTE]",
            "<blockquote class=\"callout-note\"><p><strong>NOTE:</strong>"
        )

        verdict_val = verdict.verdict.value if hasattr(verdict.verdict, "value") else str(verdict.verdict)
        verdict_color = "#10b981" if verdict_val == "APPROVED" else (
            "#ef4444" if verdict_val == "REJECTED" else "#f59e0b"
        )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Decision Dossier: {case.title} ({case.case_id})</title>
<style>
  :root {{
    --primary: #2563eb;
    --primary-dark: #1d4ed8;
    --bg: #0f172a;
    --card-bg: #1e293b;
    --text: #f1f5f9;
    --text-muted: #94a3b8;
    --border: #334155;
    --verdict-color: {verdict_color};
  }}
  * {{ box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    line-height: 1.6;
    color: #1e293b;
    background-color: #f8fafc;
    margin: 0;
    padding: 0;
  }}
  .action-bar {{
    position: sticky;
    top: 0;
    background: #0f172a;
    color: #f8fafc;
    padding: 12px 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    z-index: 1000;
  }}
  .action-bar h1 {{
    margin: 0;
    font-size: 1.1rem;
    font-weight: 600;
    letter-spacing: -0.025em;
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .btn-print {{
    background: #2563eb;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 0.9rem;
    font-weight: 600;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    transition: background 0.2s;
  }}
  .btn-print:hover {{
    background: #1d4ed8;
  }}
  .container {{
    max-width: 900px;
    margin: 40px auto;
    background: white;
    padding: 48px;
    border-radius: 12px;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.01);
    border: 1px solid #e2e8f0;
  }}
  h1 {{ font-size: 2rem; color: #0f172a; margin-top: 0; border-bottom: 2px solid #e2e8f0; padding-bottom: 12px; }}
  h2 {{ font-size: 1.4rem; color: #1e293b; margin-top: 36px; border-bottom: 1px solid #f1f5f9; padding-bottom: 8px; }}
  h3 {{ font-size: 1.15rem; color: #334155; margin-top: 24px; }}
  blockquote {{
    margin: 20px 0;
    padding: 16px 20px;
    border-left: 4px solid var(--verdict-color);
    background-color: #f8fafc;
    border-radius: 0 8px 8px 0;
    color: #334155;
  }}
  blockquote.callout-note {{
    border-left-color: #3b82f6;
    background-color: #eff6ff;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 20px 0;
    font-size: 0.95rem;
  }}
  th, td {{
    text-align: left;
    padding: 10px 14px;
    border-bottom: 1px solid #e2e8f0;
  }}
  th {{
    background-color: #f1f5f9;
    color: #475569;
    font-weight: 600;
  }}
  tr:hover td {{
    background-color: #f8fafc;
  }}
  code {{
    background: #f1f5f9;
    color: #0f172a;
    padding: 2px 6px;
    border-radius: 4px;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: 0.9em;
  }}
  hr {{
    border: none;
    border-top: 1px solid #e2e8f0;
    margin: 32px 0;
  }}
  @media print {{
    .no-print {{ display: none !important; }}
    body {{ background: white; }}
    .container {{
      max-width: 100%;
      margin: 0;
      padding: 0;
      box-shadow: none;
      border: none;
    }}
    h1, h2, h3 {{ page-break-after: avoid; }}
    table, blockquote {{ page-break-inside: avoid; }}
    @page {{ margin: 1.5cm; }}
  }}
</style>
</head>
<body>
<div class="action-bar no-print">
  <h1>
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
    Executive Decision Court Adjudication Dossier
  </h1>
  <button class="btn-print" onclick="window.print()">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 6 2 18 2 18 9"></polyline><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"></path><rect x="6" y="14" width="12" height="8"></rect></svg>
    Print / Save as PDF
  </button>
</div>
<div class="container">
  {html_body}
</div>
</body>
</html>
"""
