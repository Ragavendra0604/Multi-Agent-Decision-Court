"""
Specialized Agents package exports.
"""

from app.agents.decomposer import CaseDecomposer, DecompositionOutputSchema
from app.agents.case_analyst import CaseAnalystAgent, CaseAnalysisOutput
from app.agents.evidence_investigator import EvidenceInvestigatorAgent, ClaimInvestigationResult
from app.agents.assumption_auditor import AssumptionAuditorAgent, AssumptionAuditItem
from app.agents.logic_analyst import LogicAnalystAgent, LogicAnalysisOutput, LogicalFlaw
from app.agents.requirement_validator import RequirementValidatorAgent, RequirementAuditItem
from app.agents.theory_analyst import TheoryAnalystAgent, TheoryEvaluationItem
from app.agents.risk_analyst import RiskAnalystAgent, RiskAssessmentItem
from app.agents.alternative_generator import AlternativeGeneratorAgent, AlternativeOption, DecisionMatrixRow
from app.agents.prosecution import ProsecutionAgent, ProsecutionBatchOutput, ProsecutionArgumentItem
from app.agents.defense import DefenseAgent, DefenseBatchOutput, DefenseArgumentItem
from app.agents.cross_examiner import CrossExaminationEngine, CrossExamTurnOutput
from app.agents.judge import JudgeAgent, JudgeOutputSchema
from app.agents.sensitivity_engine import SensitivityEngine, SensitivityAnalysisOutput, WhatIfScenarioResult

__all__ = [
    "CaseDecomposer",
    "DecompositionOutputSchema",
    "CaseAnalystAgent",
    "CaseAnalysisOutput",
    "EvidenceInvestigatorAgent",
    "ClaimInvestigationResult",
    "AssumptionAuditorAgent",
    "AssumptionAuditItem",
    "LogicAnalystAgent",
    "LogicAnalysisOutput",
    "LogicalFlaw",
    "RequirementValidatorAgent",
    "RequirementAuditItem",
    "TheoryAnalystAgent",
    "TheoryEvaluationItem",
    "RiskAnalystAgent",
    "RiskAssessmentItem",
    "AlternativeGeneratorAgent",
    "AlternativeOption",
    "DecisionMatrixRow",
    "ProsecutionAgent",
    "ProsecutionBatchOutput",
    "ProsecutionArgumentItem",
    "DefenseAgent",
    "DefenseBatchOutput",
    "DefenseArgumentItem",
    "CrossExaminationEngine",
    "CrossExamTurnOutput",
    "JudgeAgent",
    "JudgeOutputSchema",
    "SensitivityEngine",
    "SensitivityAnalysisOutput",
    "WhatIfScenarioResult",
]
