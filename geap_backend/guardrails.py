"""Enterprise Guardrails and Self-Evaluation Engine for Apex Wireless Agents.

Complies with AgentOps Code Review Matrix:
- Guardrails & Policy Plugins: Input prompt injection detection and output self-evaluation.
- Enforces corporate security policies and telephone safety guidelines.
"""

import re
from typing import Any, Dict, List, Optional
from observability import logger

# Blocklist patterns for prompt injection, jailbreaking, and system extraction
PROMPT_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior)\s+instructions", re.IGNORECASE),
    re.compile(r"reveal\s+(your\s+)?(system\s+prompt|instructions|constitution)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(in\s+developer\s+mode|dan|unrestricted)", re.IGNORECASE),
    re.compile(r"print\s+(secret|password|api[_\s]?key|auth[_\s]?token)", re.IGNORECASE),
    re.compile(r"system\s*:\s*override", re.IGNORECASE),
]

# Sensitive tokens that should never leak in conversational outputs
LEAK_PATTERNS = [
    re.compile(r"APEX_AUTH_TOKEN", re.IGNORECASE),
    re.compile(r"apex-enterprise-secret-token", re.IGNORECASE),
    re.compile(r"BEGIN PRIVATE KEY", re.IGNORECASE),
]


def validate_input_guardrail(user_input: str, session_id: str = "default") -> Dict[str, Any]:
    """Validates inbound user speech/text against prompt injection and security policies.

    Args:
        user_input: The text query spoken or typed by the customer.
        session_id: Current conversation session identifier.

    Returns:
        Dict indicating whether input passed guardrails, with violation reason if blocked.
    """
    if not user_input or not user_input.strip():
        return {"passed": True, "violation": None}

    cleaned = user_input.strip()

    for pattern in PROMPT_INJECTION_PATTERNS:
        if pattern.search(cleaned):
            logger.warning(
                f"SECURITY GUARDRAIL TRIGGERED: Detected potential prompt injection: '{cleaned}'",
                extra={"session_id": session_id, "stage": "guardrail_violation", "metadata": {"policy": "ANTI_PROMPT_INJECTION"}},
            )
            return {
                "passed": False,
                "violation": "PROMPT_INJECTION_DETECTED",
                "safe_fallback": (
                    "I am sorry, but I can only assist with Apex Wireless accounts, "
                    "device sales, technical diagnostics, and billing questions."
                ),
            }

    return {"passed": True, "violation": None}


def validate_output_guardrail(agent_response: str, session_id: str = "default") -> Dict[str, Any]:
    """Self-evaluates model response to ensure zero credential leakage and telephone compliance.

    Args:
        agent_response: The generated text response destined for TTS synthesis.
        session_id: Current conversation session identifier.

    Returns:
        Dict indicating whether output passed guardrails.
    """
    if not agent_response:
        return {"passed": True, "sanitized_response": ""}

    for pattern in LEAK_PATTERNS:
        if pattern.search(agent_response):
            logger.error(
                "OUTPUT GUARDRAIL TRIGGERED: Attempted credential/system instruction leak",
                extra={"session_id": session_id, "stage": "output_guardrail_violation"},
            )
            return {
                "passed": False,
                "violation": "CREDENTIAL_LEAK_DETECTED",
                "sanitized_response": "I apologize, but I am unable to process that internal request. How can I help with your wireless service?",
            }

    # Telephony markdown cleanup guardrail
    # Ensure no asterisks or markdown formatting slips into voice synthesis
    cleaned_voice_response = re.sub(r"\*\*([^*]+)\*\*", r"\1", agent_response)
    cleaned_voice_response = re.sub(r"^\s*[-*]\s+", "", cleaned_voice_response, flags=re.MULTILINE)

    return {
        "passed": True,
        "violation": None,
        "sanitized_response": cleaned_voice_response,
    }
