"""
Structured Output Reliability Layer.
Implements Module 28: JSON extraction, schema validation, repair prompt, retry, and fallback.
"""

import json
import re
from typing import Any, Dict, Optional, Type, TypeVar
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


def extract_json_candidate(raw_text: str) -> str:
    """
    Extracts JSON from markdown code blocks or finds the largest balanced JSON object/array.
    """
    if not raw_text:
        return ""
    
    text = raw_text.strip()
    
    # Strip <think> ... </think> or <reasoning> ... </reasoning> blocks if present
    text = re.sub(r"<(think|reasoning)>[\s\S]*?</\1>", "", text, flags=re.IGNORECASE).strip()
    
    # 1. Check markdown fenced code blocks ```json ... ```
    json_block_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if json_block_match:
        candidate = json_block_match.group(1).strip()
        if (candidate.startswith("{") and candidate.endswith("}")) or (
            candidate.startswith("[") and candidate.endswith("]")
        ):
            return candidate

    # 2. Find outermost balanced braces {...}
    start_brace = text.find("{")
    end_brace = text.rfind("}")
    if start_brace != -1 and end_brace != -1 and end_brace > start_brace:
        return text[start_brace : end_brace + 1]

    # 3. Find outermost balanced brackets [...]
    start_bracket = text.find("[")
    end_bracket = text.rfind("]")
    if start_bracket != -1 and end_bracket != -1 and end_bracket > start_bracket:
        return text[start_bracket : end_bracket + 1]

    return text


import ast

def repair_common_json_issues(json_str: str) -> str:
    """
    Attempts repairs on common LLM JSON syntax errors (trailing commas, single quotes, unescaped quotes).
    """
    s = json_str.strip()
    
    # Try ast.literal_eval if it is a python dict literal (single quotes, True/False)
    try:
        py_obj = ast.literal_eval(s)
        if isinstance(py_obj, (dict, list)):
            return json.dumps(py_obj)
    except Exception:
        pass
    
    # Remove trailing commas before closing braces/brackets
    s = re.sub(r",\s*([\}\]])", r"\1", s)
    
    # Replace single quotes with double quotes
    s = re.sub(r"\'([a-zA-Z0-9_\-]+)\'\s*:", r'"\1":', s)
    s = re.sub(r":\s*\'([^\']*)\'", r': "\1"', s)
    
    # Fix boolean/null literals
    s = re.sub(r"\bTrue\b", "true", s)
    s = re.sub(r"\bFalse\b", "false", s)
    s = re.sub(r"\bNone\b", "null", s)
    
    return s


def parse_and_validate_json(raw_text: str, schema: Type[T]) -> T:
    """
    Attempts to extract, repair, parse and validate JSON against a Pydantic schema.
    Raises ValueError or ValidationError if parsing fails.
    """
    candidate = extract_json_candidate(raw_text)
    if not candidate:
        raise ValueError("No JSON object or array found in model response.")

    try:
        data = json.loads(candidate)
    except json.JSONDecodeError:
        repaired = repair_common_json_issues(candidate)
        try:
            data = json.loads(repaired)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON syntax error: {e}. Raw content: {candidate[:200]}...") from e

    return schema.model_validate(data)


def parse_float_safe(val: Any, default: float = 0.5) -> float:
    """
    Safely converts arbitrary values (strings, words, percentages, out-of-bound numbers)
    into a valid normalized float between 0.0 and 1.0.
    """
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return max(0.0, min(1.0, float(val)))
    val_str = str(val).strip().lower()
    if val_str in ("very high", "critical"):
        return 0.95
    if val_str in ("high", "severe", "major", "strong"):
        return 0.8
    if val_str in ("medium", "moderate", "normal", "average"):
        return 0.5
    if val_str in ("low", "minor", "weak"):
        return 0.2
    if val_str in ("very low", "negligible", "minimal"):
        return 0.05
    try:
        match = re.search(r"[-+]?\d*\.?\d+", val_str)
        if match:
            num = float(match.group(0))
            if 1.0 < num <= 100.0:
                num = num / 100.0
            return max(0.0, min(1.0, num))
    except Exception:
        pass
    return default

