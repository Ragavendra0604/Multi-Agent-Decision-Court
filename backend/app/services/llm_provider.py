"""
LLM Provider Abstraction & Reliable Structured Execution.
Implements Module 27 (LLM Provider Abstraction), Module 28 (Structured Output Reliability),
and Module 46 (Cost & Fallback Management).
"""

from abc import ABC, abstractmethod
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Type, TypeVar
import httpx
from pydantic import BaseModel, ValidationError

from app.config import settings
from app.services.structured_output import parse_and_validate_json

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMMessage(BaseModel):
    role: str
    content: str


class LLMResponse(BaseModel):
    content: str
    raw_response: Optional[Dict[str, Any]] = None
    model: str
    usage: Dict[str, Any] = {}
    provider: str


class BaseLLMProvider(ABC):
    def __init__(self, model_name: str, api_key: Optional[str] = None, timeout: float = 60.0):
        self.model_name = model_name
        self.api_key = api_key
        self.timeout = timeout

    @abstractmethod
    async def generate_text(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.2,
        max_tokens: Optional[int] = 1536,
        model_override: Optional[str] = None,
    ) -> LLMResponse:
        pass


class MockLLMProvider(BaseLLMProvider):
    """
    Mock LLM provider for zero-cost testing, deterministic execution, and offline development.
    """
    async def generate_text(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.2,
        max_tokens: Optional[int] = 1536,
        model_override: Optional[str] = None,
    ) -> LLMResponse:
        # Check system prompt or last message to return context-aware JSON responses
        last_msg = messages[-1].content if messages else ""
        system_msg = next((m.content for m in messages if m.role == "system"), "")
        
        # Dynamic deterministic mock response generator based on schema requested
        if "Judge" in system_msg:
            mock_content = json.dumps({
                "verdict": "PARTIALLY_VALID",
                "confidence": 0.78,
                "correctness_status": "LIKELY_VALID",
                "correctness_confidence": 0.75,
                "correctness_summary": "The proposed decision aligns with performance objectives but lacks cost guarantees.",
                "justification_status": "PARTIAL",
                "justification_confidence": 0.65,
                "justification_summary": "Key performance claims are evidenced, but budget assumptions remain unverified.",
                "summary_verdict_rationale": "Solution X demonstrates valid technical viability; however, financial claims lack verified data.",
                "unresolved_questions": ["What is the total cloud egress cost at peak scale?"],
                "missing_information": ["Official third-party SLA verification report."],
                "critical_decision_drivers": ["Performance SLA compliance", "Budget feasibility"],
                "recommended_next_actions": ["Request vendor benchmark audit", "Perform pilot migration on non-critical service"]
            })
        elif "Case Analyst" in system_msg:
            mock_content = json.dumps({
                "objective": "Determine whether migrating to Solution X meets performance and cost goals.",
                "scope": "In-scope: Database and API layer. Out-of-scope: Frontend and analytics redesign.",
                "ambiguities_detected": ["Term 'faster' lacks target latency percentile.", "Vague definition of 'lower overhead'."],
                "missing_context": ["Current production CPU utilization metrics."],
                "atomic_claims": [
                    {"statement": "Solution X reduces operational overhead by 40%", "category": "Cost", "is_core": True},
                    {"statement": "Solution X provides 99.99% availability", "category": "Performance", "is_core": True}
                ],
                "confidence": 0.85
            })
        elif "Evidence Investigator" in system_msg:
            mock_content = json.dumps({
                "investigations": [
                    {
                        "claim_id": "C-01",
                        "status": "SUPPORTED",
                        "confidence": 0.88,
                        "relevance_score": 0.90,
                        "reliability_score": 0.85,
                        "directness": "DIRECT",
                        "supporting_evidence_ids": ["E-01"],
                        "contradicting_evidence_ids": [],
                        "findings_summary": "Synthetic benchmark results directly demonstrate 40% latency reduction.",
                        "missing_evidence_notes": None
                    },
                    {
                        "claim_id": "C-02",
                        "status": "PARTIALLY_SUPPORTED",
                        "confidence": 0.60,
                        "relevance_score": 0.75,
                        "reliability_score": 0.70,
                        "directness": "INDIRECT",
                        "supporting_evidence_ids": [],
                        "contradicting_evidence_ids": ["E-02"],
                        "findings_summary": "Cost reductions are offset by higher cloud egress rates in pricing documentation.",
                        "missing_evidence_notes": "No production billing invoice available."
                    }
                ]
            })
        elif "Assumption Auditor" in system_msg:
            mock_content = json.dumps({
                "audited_assumptions": [
                    {
                        "assumption_id": "A-01",
                        "statement": "Current staff can transition without full retraining",
                        "is_explicit": False,
                        "status": "QUESTIONABLE",
                        "validity_score": 0.45,
                        "criticality": 0.80,
                        "dependent_claim_ids": ["C-01"],
                        "rationale": "Solution X uses a proprietary query language requiring substantial learning curve.",
                        "risks_if_invalid": "Migration schedule delayed by 3 months."
                    }
                ],
                "uncovered_hidden_assumptions": [
                    {
                        "assumption_id": "A-HIDDEN-01",
                        "statement": "Network bandwidth between cloud zones is unthrottled",
                        "is_explicit": False,
                        "status": "UNVERIFIED",
                        "validity_score": 0.50,
                        "criticality": 0.75,
                        "dependent_claim_ids": ["C-02"],
                        "rationale": "High throughput replication requires dedicated interconnects.",
                        "risks_if_invalid": "Replication lag under heavy traffic."
                    }
                ]
            })
        elif "Logic Analyst" in system_msg:
            mock_content = json.dumps({
                "overall_logical_validity_score": 0.68,
                "reasoning_structure_soundness": "WEAK",
                "flaws_detected": [
                    {
                        "flaw_type": "Correlation versus causation",
                        "description": "Assuming lower raw database latency will automatically decrease end-to-end user checkout time without checking network roundtrips.",
                        "affected_claims": ["C-01"],
                        "severity": 0.70,
                        "remedy_suggestion": "Measure frontend-to-gateway telemetry."
                    }
                ],
                "unsupported_leaps": ["Inference that lower license fees will overcome higher hosting egress charges."],
                "summary": "Reasoning chain contains an unsupported inductive leap regarding total cost of ownership."
            })
        elif "Requirement Validator" in system_msg:
            mock_content = json.dumps({
                "overall_satisfaction_score": 0.72,
                "has_critical_violation": False,
                "evaluations": [
                    {
                        "req_id": "R-01",
                        "description": "Keep migration budget under $100k",
                        "is_critical_constraint": True,
                        "status": "PARTIALLY_SATISFIED",
                        "satisfaction_score": 0.65,
                        "supporting_factors": ["Initial licensing cost is within budget"],
                        "violating_factors": ["Staff training and overtime costs not factored"],
                        "justification": "Base software cost is compliant, but contingency buffer is minimal."
                    }
                ],
                "summary": "Critical budget constraint is at risk of partial overrun."
            })
        elif "Theory Analyst" in system_msg:
            mock_content = json.dumps({
                "evaluations": [
                    {
                        "theory_id": "T-01",
                        "name": "Horizontal scaling economy",
                        "preconditions_satisfied": True,
                        "applicability_score": 0.80,
                        "limitations_identified": ["Requires stateless microservices layer"],
                        "confidence": 0.85,
                        "evaluation_summary": "Theory applies well to the stateless API layer."
                    }
                ],
                "summary": "Theoretical models support architectural scaling."
            })
        elif "Risk Analyst" in system_msg:
            mock_content = json.dumps({
                "overall_risk_level": "MODERATE",
                "max_severity": 0.65,
                "identified_risks": [
                    {
                        "risk_id": "RISK-01",
                        "category": "TECHNICAL",
                        "description": "Vendor API deprecation and lock-in",
                        "probability": 0.50,
                        "impact": 0.80,
                        "severity_score": 0.40,
                        "mitigation_suggested": "Build an abstraction interface layer around vendor SDK",
                        "affected_claim_ids": ["C-01"]
                    }
                ],
                "executive_risk_summary": "Key technical risks stem from vendor dependency."
            })
        elif "Alternative Generator" in system_msg:
            mock_content = json.dumps({
                "proposed_decision_summary": "Full migration to Solution X",
                "alternatives": [
                    {
                        "alt_id": "ALT-01",
                        "title": "In-house database indexing & caching optimization",
                        "category": "Optimize current solution",
                        "description": "Add Redis caching tier and optimize Postgres indices.",
                        "pros": ["Zero migration risk", "Negligible license cost"],
                        "cons": ["Limited to 2x speedup rather than 5x"],
                        "estimated_feasibility": 0.90,
                        "requirement_fit_score": 0.80,
                        "tradeoff_summary": "Much cheaper with lower performance ceiling."
                    }
                ],
                "decision_matrix": [
                    {
                        "criterion": "Cost",
                        "proposed_decision_score": 6.5,
                        "alternatives_scores": {"ALT-01": 9.0},
                        "rationale": "In-house optimization avoids new software licensing."
                    },
                    {
                        "criterion": "Performance",
                        "proposed_decision_score": 9.0,
                        "alternatives_scores": {"ALT-01": 7.0},
                        "rationale": "Solution X offers superior distributed throughput."
                    }
                ],
                "recommendation_commentary": "Consider optimizing existing stack before committing to full rewrite."
            })
        elif "Sensitivity" in system_msg:
            mock_content = json.dumps({
                "most_fragile_assumptions": ["A-01: Zero retraining required for engineering staff"],
                "critical_cost_or_risk_thresholds": ["Migration cost exceeds $100k", "Cross-zone egress bandwidth exceeds 10Gbps"],
                "scenarios": [
                    {
                        "scenario_id": "SCEN-01",
                        "scenario_title": "Staff Training Delay",
                        "condition_tested": "What if staff retraining takes 3 months instead of zero time?",
                        "verdict_impact": "DOWNGRADED_TO_PARTIALLY_VALID",
                        "tipping_point_threshold": "Retraining cost > $25k",
                        "recommended_pivot": "Adopt hybrid phased rollout or hire 2 experienced contractors",
                        "rationale": "Overtime costs breach the $100k hard budget constraint."
                    },
                    {
                        "scenario_id": "SCEN-02",
                        "scenario_title": "Egress Cost Spike",
                        "condition_tested": "What if network egress fee doubles at 50k RPS?",
                        "verdict_impact": "FLIPPED_TO_INVALID",
                        "tipping_point_threshold": "Egress fee > $0.08 per GB",
                        "recommended_pivot": "Implement local Redis edge caching (Alternative ALT-01)",
                        "rationale": "Operating cost becomes 15% higher than the legacy system."
                    }
                ],
                "robustness_score": 0.65
            })
        elif "Cross-Examination" in system_msg or "Cross-Examiner" in system_msg:
            mock_content = json.dumps({
                "challenge": "Synthetic benchmarks do not reflect realistic multi-region database latency under network jitter.",
                "defense_response": "We have included a 25% safety margin in throughput estimates and will enforce regional replication.",
                "counter_challenge": "Safety margin does not mitigate edge node packet loss.",
                "resolution_state": "PARTIALLY_RESOLVED",
                "unresolved_uncertainty": "Exact network jitter behavior across secondary regions remains unmeasured.",
                "terminate_debate": True
            })
        elif "Evidence Reconciliation" in system_msg:
            mock_content = json.dumps({
                "reconciled_items": [
                    {
                        "topic_or_claim_id": "C-02",
                        "conflicting_evidence_ids": ["E-01", "E-02"],
                        "status": "PARTIALLY_RESOLVED",
                        "resolution_rationale": "Performance gains are validated, but egress pricing documentation overrides optimistic initial cost projections.",
                        "authority_comparison": "Vendor official pricing sheet carries higher legal and contractual authority than vendor marketing slides.",
                        "date_comparison": "Pricing sheet dated Q4 2025 is more recent than initial whitepaper.",
                        "applicability_comparison": "Direct production workload parameters apply."
                    }
                ],
                "summary": "Financial conflicts resolved against the initial optimistic claim due to newer pricing data."
            })
        elif "Prosecution" in system_msg:
            mock_content = json.dumps({
                "prosecution_case_summary": "The proposed decision suffers from unverified egress cost inflation and hidden migration downtime.",
                "arguments": [
                    {
                        "title": "Unverified vendor cost trajectory",
                        "target_claim_id": "C-02",
                        "target_assumption_id": None,
                        "statement": "The projected 40% savings fail to account for escalating API ingress/egress fees.",
                        "supporting_evidence_ids": ["E-02"],
                        "confidence": 0.82,
                        "severity_or_strength": 0.85,
                        "challenge_category": "Hidden cost"
                    }
                ],
                "critical_vulnerabilities": ["Budget overrun from egress fees", "Lack of rollback plan"]
            })
        elif "Defense" in system_msg:
            mock_content = json.dumps({
                "defense_case_summary": "The migration to Solution X is justified by validated 40% latency improvements and automated scaling.",
                "arguments": [
                    {
                        "title": "Proven performance headroom",
                        "target_claim_id": "C-01",
                        "statement": "Benchmark evidence confirms 3x latency reduction under synthetic load tests.",
                        "supporting_evidence_ids": ["E-01"],
                        "confidence": 0.88,
                        "severity_or_strength": 0.80,
                        "defense_strategy": "Direct evidence backing"
                    }
                ],
                "concessions_made": [
                    {
                        "weakness_area": "Egress cost uncertainty",
                        "concession_summary": "Direct egress costs have not been measured against multi-region replication.",
                        "mitigation_or_contingency": "Deploy egress caching layer and conduct 1-month staging pilot."
                    }
                ]
            })
        elif "Case Decomposer" in system_msg or "Decompose" in system_msg:
            mock_content = json.dumps({
                "title": "Migrate to Solution X",
                "problem": "Legacy system is high latency and expensive to maintain",
                "proposed_decision": "Migrate workload to Solution X",
                "context": "Enterprise SaaS backend handling 50k RPS.",
                "requirements": [
                    "Keep total migration budget under $100k",
                    "Maintain 99.99% service availability"
                ],
                "constraints": [
                    "Must be completed within 6 months"
                ],
                "claims": [
                    {"statement": "Solution X reduces operational overhead by 40%", "category": "Cost", "is_core": True},
                    {"statement": "Solution X provides 99.99% service availability", "category": "Performance", "is_core": True}
                ],
                "assumptions": [
                    {"statement": "Current staff can transition without full retraining", "is_explicit": False, "criticality": 0.8}
                ],
                "theories": [
                    {"name": "Horizontal scaling economy", "preconditions": ["Stateless app architecture"]}
                ],
                "risks": [
                    {"description": "Potential vendor lock-in", "category": "TECHNICAL", "probability": 0.4, "impact": 0.7}
                ],
                "alternatives": [
                    {"title": "Optimize legacy system in-house", "description": "Refactor existing monolith", "category": "Optimize current solution"}
                ],
                "missing_information": [
                    "Exact breakdown of cloud network egress costs"
                ]
            })
        else:
            mock_content = json.dumps({
                "status": "SUCCESS",
                "message": "Processed successfully by MockLLMProvider",
                "analysis": "Mock analysis output."
            })
            
        return LLMResponse(
            content=mock_content,
            model=model_override or self.model_name,
            usage={"prompt_tokens": 100, "completion_tokens": 80, "total_tokens": 180},
            provider="mock"
        )


class OpenRouterProvider(BaseLLMProvider):
    """
    OpenRouter API provider supporting hundreds of models with unified interface.
    """
    def __init__(self, model_name: str, api_key: Optional[str] = None, timeout: float = 60.0):
        super().__init__(model_name, api_key or settings.OPENROUTER_API_KEY, timeout)
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

    async def generate_text(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.2,
        max_tokens: Optional[int] = 1536,
        model_override: Optional[str] = None,
    ) -> LLMResponse:
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY is not configured.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/agentic-court",
            "X-Title": settings.APP_NAME,
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": model_override or self.model_name,
            "messages": [m.model_dump() for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(self.base_url, headers=headers, json=payload)
            if response.status_code != 200:
                raise RuntimeError(f"OpenRouter error {response.status_code}: {response.text}")
            
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            return LLMResponse(
                content=content,
                raw_response=data,
                model=model_override or self.model_name,
                usage=usage,
                provider="openrouter",
            )


class HuggingFaceProvider(BaseLLMProvider):
    """
    Hugging Face Router / Inference API provider.
    """
    def __init__(self, model_name: str, api_key: Optional[str] = None, timeout: float = 60.0):
        super().__init__(model_name, api_key or settings.HUGGINGFACE_API_KEY, timeout)
        self.base_url = f"https://api-inference.huggingface.co/models/{model_name}"

    async def generate_text(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.2,
        max_tokens: Optional[int] = 1536,
        model_override: Optional[str] = None,
    ) -> LLMResponse:
        if not self.api_key:
            raise ValueError("HUGGINGFACE_API_KEY is not configured.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        prompt_text = "\n".join([f"[{m.role.upper()}]: {m.content}" for m in messages])
        payload = {
            "inputs": prompt_text,
            "parameters": {
                "temperature": temperature,
                "max_new_tokens": max_tokens,
                "return_full_text": False,
            }
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(self.base_url, headers=headers, json=payload)
            if response.status_code != 200:
                raise RuntimeError(f"Hugging Face error {response.status_code}: {response.text}")
            
            data = response.json()
            content = data[0]["generated_text"] if isinstance(data, list) and data else str(data)
            return LLMResponse(
                content=content,
                raw_response=data if isinstance(data, dict) else {},
                model=model_override or self.model_name,
                usage={},
                provider="huggingface",
            )


class OpenAICompatibleProvider(BaseLLMProvider):
    """
    Generic OpenAI-compatible provider (OpenAI, Local Ollama, vLLM, Groq).
    """
    def __init__(
        self,
        model_name: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 60.0,
    ):
        super().__init__(model_name, api_key or settings.OPENAI_API_KEY or "dummy", timeout)
        self.base_url = (base_url or settings.OPENAI_BASE_URL or "https://api.openai.com/v1").rstrip("/") + "/chat/completions"

    async def generate_text(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.2,
        max_tokens: Optional[int] = 1536,
        model_override: Optional[str] = None,
    ) -> LLMResponse:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model_override or self.model_name,
            "messages": [m.model_dump() for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(self.base_url, headers=headers, json=payload)
            if response.status_code != 200:
                raise RuntimeError(f"OpenAI compatible endpoint error {response.status_code}: {response.text}")
            
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return LLMResponse(
                content=content,
                raw_response=data,
                model=model_override or self.model_name,
                usage=data.get("usage", {}),
                provider="openai-compatible",
            )


class GroqProvider(BaseLLMProvider):
    """
    Dedicated Groq Cloud provider with ultra-fast inference and JSON object mode.
    """
    def __init__(
        self,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 60.0,
    ):
        model = model_name or settings.GROQ_MODEL or settings.LLM_MODEL or "openai/gpt-oss-120b"
        key = api_key or settings.GROQ_API_KEY or settings.OPENAI_API_KEY
        super().__init__(model, key, timeout)
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"

    async def generate_text(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.2,
        max_tokens: Optional[int] = 1536,
        model_override: Optional[str] = None,
    ) -> LLMResponse:
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is not configured. Please set it in your .env file.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model_override or self.model_name,
            "messages": [m.model_dump() for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(self.base_url, headers=headers, json=payload)
            if response.status_code != 200:
                raise RuntimeError(f"Groq API error {response.status_code}: {response.text}")

            data = response.json()
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            return LLMResponse(
                content=content,
                raw_response=data,
                model=model_override or self.model_name,
                usage=usage,
                provider="groq",
            )


class CascadingLLMProvider(BaseLLMProvider):
    """
    Resilient multi-provider manager that chains LLM providers in sequence.
    If the primary provider (e.g. Groq) encounters rate limits (429), token quotas,
    or service errors, it seamlessly fails over to the secondary provider (e.g. OpenRouter).
    """
    def __init__(self, providers: List[BaseLLMProvider]):
        primary = providers[0] if providers else MockLLMProvider("mock")
        super().__init__(model_name=primary.model_name, api_key=primary.api_key, timeout=primary.timeout)
        self.providers = providers
        self.provider = "cascading"

    async def generate_text(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.2,
        max_tokens: Optional[int] = 1536,
        model_override: Optional[str] = None,
    ) -> LLMResponse:
        errors = []
        for i, p in enumerate(self.providers):
            try:
                resp = await p.generate_text(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    model_override=model_override if i == 0 else None,
                )
                if i > 0:
                    logger.info(f"CascadingLLMProvider: served request via fallback provider '{getattr(p, 'provider', type(p).__name__)}'")
                return resp
            except Exception as e:
                p_name = getattr(p, "provider", type(p).__name__)
                err_msg = f"{p_name} ({p.model_name}): {e}"
                logger.warning(f"Provider failed in cascade: {err_msg}. Failing over to next provider...")
                errors.append(err_msg)

        raise RuntimeError(f"All providers in cascade failed: {'; '.join(errors)}")


def get_llm_provider(
    provider_name: Optional[str] = None,
    model_name: Optional[str] = None,
    enable_cascade: bool = True,
) -> BaseLLMProvider:
    """
    Factory function returning the configured LLM provider, with multi-provider
    automatic failover cascade enabled by default.
    """
    name = (provider_name or settings.LLM_PROVIDER).lower()
    
    if name == "mock":
        return MockLLMProvider(model_name=model_name or settings.LLM_MODEL)

    if not enable_cascade or not getattr(settings, "ENABLE_CASCADE", True):
        model = model_name or (settings.GROQ_MODEL if name == "groq" else settings.LLM_MODEL)
        if name == "groq":
            return GroqProvider(model_name=model)
        elif name == "openrouter":
            return OpenRouterProvider(model_name=model)
        elif name == "huggingface":
            return HuggingFaceProvider(model_name=model)
        elif name in ("openai", "custom"):
            return OpenAICompatibleProvider(model_name=model)
        return MockLLMProvider(model_name=model)

    chain: List[BaseLLMProvider] = []
    if name == "groq":
        if settings.GROQ_API_KEY:
            chain.append(GroqProvider(model_name=model_name or settings.GROQ_MODEL))
        if settings.OPENROUTER_API_KEY:
            chain.append(OpenRouterProvider(model_name=settings.OPENROUTER_MODEL))
    elif name == "openrouter":
        if settings.OPENROUTER_API_KEY:
            chain.append(OpenRouterProvider(model_name=model_name or settings.OPENROUTER_MODEL))
        if settings.GROQ_API_KEY:
            chain.append(GroqProvider(model_name=settings.GROQ_MODEL))
    elif name in ("openai", "custom"):
        chain.append(OpenAICompatibleProvider(model_name=model_name or settings.LLM_MODEL))
        if settings.GROQ_API_KEY:
            chain.append(GroqProvider(model_name=settings.GROQ_MODEL))

    if not chain:
        chain.append(MockLLMProvider(model_name="mock"))

    return CascadingLLMProvider(chain) if len(chain) > 1 else chain[0]

async def execute_structured_prompt(
    provider: BaseLLMProvider,
    messages: List[LLMMessage],
    schema: Type[T],
    temperature: float = 0.2,
    max_retries: int = 3,
    fallback_model: Optional[str] = None,
) -> T:
    """
    Executes an LLM call with automated schema validation, repair prompts, retry loops,
    and fallback model escalation (Module 28).
    """
    schema_json_schema = json.dumps(schema.model_json_schema(), indent=2)
    augmented_messages = list(messages)
    
    # Append instructions to guarantee strict JSON output matching schema
    json_instruction = (
        f"\n\nCRITICAL: Respond ONLY with valid JSON conforming to the following JSON Schema. "
        f"Do not include any conversational preamble, commentary, or postscript outside the JSON structure:\n"
        f"```json\n{schema_json_schema}\n```"
    )
    
    if augmented_messages:
        augmented_messages[-1] = LLMMessage(
            role=augmented_messages[-1].role,
            content=augmented_messages[-1].content + json_instruction
        )
    else:
        augmented_messages.append(LLMMessage(role="user", content=json_instruction))

    current_messages = list(augmented_messages)
    last_error: Optional[Exception] = None

    for attempt in range(1, max_retries + 1):
        try:
            effective_fallback = fallback_model or settings.FALLBACK_LLM_MODEL
            model_to_use = effective_fallback if (attempt >= 2 and effective_fallback) else None
            response = await provider.generate_text(
                messages=current_messages,
                temperature=temperature,
                model_override=model_to_use
            )
            parsed_object = parse_and_validate_json(response.content, schema)
            return parsed_object
        except (ValueError, ValidationError, json.JSONDecodeError) as e:
            last_error = e
            logger.warning(f"Structured output attempt {attempt} failed: {e}. Attempting auto-repair...")
            # Inject repair prompt
            current_messages.append(LLMMessage(
                role="assistant",
                content=response.content if 'response' in locals() else ""
            ))
            current_messages.append(LLMMessage(
                role="user",
                content=(
                    f"Your previous response failed validation with error: {str(e)}.\n"
                    f"Please correct the JSON output and ensure strict adherence to the schema. "
                    f"Return ONLY valid JSON."
                )
            ))
            await asyncio.sleep(0.5 * attempt)
        except Exception as e:
            last_error = e
            logger.error(f"Provider generation error on attempt {attempt}: {e}")
            import re
            err_str = str(e)
            match = re.search(r"try again in ([\d\.]+)s", err_str)
            if match:
                wait_time = float(match.group(1)) + 1.2
                logger.info(f"Rate limited by provider. Sleeping for {wait_time:.1f}s before retry...")
                await asyncio.sleep(wait_time)
            elif "429" in err_str:
                await asyncio.sleep(5.0 * attempt)
            else:
                await asyncio.sleep(1.0 * attempt)

    raise ValueError(f"Failed to generate structured output after {max_retries} attempts. Error: {last_error}")
