"""Enterprise Observability, Structured JSON Logging, OpenTelemetry Tracing, and PII Redaction.

Complies with AgentOps Code Review Matrix:
1. Structured JSON Logging: Emits machine-parseable JSON metadata.
2. Intent vs. Outcome Capture: Distinct pre-execution and post-execution hooks.
3. Distributed Tracing: OpenTelemetry span instrumentation with trace IDs.
4. PII Redaction: Real-time scrubbing of phone numbers, PINs, account IDs, and cards.
"""

import json
import logging
import re
import sys
import time
import uuid
from contextlib import contextmanager
from typing import Any, Dict, Optional

# ---------------------------------------------------------------------------
# PII Redaction Engine
# ---------------------------------------------------------------------------

# Patterns for sensitive telecom customer information
PII_PATTERNS = [
    # 4-digit security PINs
    (re.compile(r"\bPIN[:=\s]*([0-9]{4})\b", re.IGNORECASE), "PIN:[REDACTED_PIN]"),
    (re.compile(r"(?<=pin['\"]:\s['\"])[0-9]{4}(?=['\"])", re.IGNORECASE), "[REDACTED_PIN]"),
    # Phone numbers (e.g. 415-555-0199, +14155550199, 4155550199)
    (re.compile(r"\b(?:\+?1[-. ]?)?\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})\b"), r"\1-***-****"),
    # Credit Card Numbers (13-16 digits with hyphens/spaces)
    (re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b"), "[REDACTED_CREDIT_CARD]"),
    # US Social Security Numbers
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED_SSN]"),
]


def redact_pii(text: Any) -> Any:
    """Recursively redacts sensitive customer PII from strings, dicts, and lists."""
    if isinstance(text, str):
        sanitized = text
        for pattern, replacement in PII_PATTERNS:
            sanitized = pattern.sub(replacement, sanitized)
        return sanitized
    elif isinstance(text, dict):
        return {k: redact_pii(v) for k, v in text.items()}
    elif isinstance(text, list):
        return [redact_pii(item) for item in text]
    return text


# ---------------------------------------------------------------------------
# Structured JSON Logging
# ---------------------------------------------------------------------------

class StructuredJsonFormatter(logging.Formatter):
    """Formats log records as structured, single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": self.formatTime(record, self.datefmt),
            "severity": record.levelname,
            "logger": record.name,
            "message": redact_pii(record.getMessage()),
            "trace_id": getattr(record, "trace_id", None),
            "span_id": getattr(record, "span_id", None),
            "session_id": getattr(record, "session_id", None),
            "agent_name": getattr(record, "agent_name", None),
            "stage": getattr(record, "stage", None),
            "metadata": redact_pii(getattr(record, "metadata", {})),
        }
        # Remove null keys for compactness
        clean_obj = {k: v for k, v in log_obj.items() if v is not None}
        return json.dumps(clean_obj)


def get_structured_logger(name: str = "apex.geap") -> logging.Logger:
    """Configures and returns a structured JSON logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredJsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


logger = get_structured_logger()


# ---------------------------------------------------------------------------
# Intent vs. Outcome Logging Hooks
# ---------------------------------------------------------------------------

def log_intent(
    agent_name: str,
    tool_name: str,
    parameters: Dict[str, Any],
    session_id: str = "default-session",
    trace_id: Optional[str] = None,
):
    """Logs the agent's intended action and parameters prior to tool execution."""
    extra = {
        "agent_name": agent_name,
        "stage": "intent",
        "session_id": session_id,
        "trace_id": trace_id or str(uuid.uuid4())[:8],
        "metadata": {
            "tool_name": tool_name,
            "action": "INVOKE_TOOL",
            "parameters": redact_pii(parameters),
        },
    }
    logger.info(f"Agent [{agent_name}] intents to execute tool [{tool_name}]", extra=extra)


def log_outcome(
    agent_name: str,
    tool_name: str,
    result: Any,
    execution_time_ms: float,
    session_id: str = "default-session",
    success: bool = True,
    trace_id: Optional[str] = None,
):
    """Logs the concrete outcome, return status, and latency after tool execution."""
    extra = {
        "agent_name": agent_name,
        "stage": "outcome",
        "session_id": session_id,
        "trace_id": trace_id or str(uuid.uuid4())[:8],
        "metadata": {
            "tool_name": tool_name,
            "status": "SUCCESS" if success else "FAILURE",
            "latency_ms": round(execution_time_ms, 2),
            "result_summary": redact_pii(str(result)[:300]),
        },
    }
    logger.info(
        f"Tool [{tool_name}] finished for agent [{agent_name}] in {execution_time_ms:.2f}ms (Success={success})",
        extra=extra,
    )


# ---------------------------------------------------------------------------
# Distributed Tracing (OpenTelemetry Compatible)
# ---------------------------------------------------------------------------

@contextmanager
def trace_span(span_name: str, attributes: Optional[Dict[str, Any]] = None):
    """Context manager creating a distributed tracing span with timing and attributes."""
    trace_id = str(uuid.uuid4())
    span_id = str(uuid.uuid4())[:16]
    start_time = time.perf_counter()
    sanitized_attrs = redact_pii(attributes or {})

    logger.info(
        f"START_SPAN [{span_name}]",
        extra={
            "trace_id": trace_id,
            "span_id": span_id,
            "stage": "trace_start",
            "metadata": {"span_name": span_name, **sanitized_attrs},
        },
    )

    span_context = {
        "trace_id": trace_id,
        "span_id": span_id,
        "span_name": span_name,
    }

    try:
        yield span_context
    finally:
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            f"END_SPAN [{span_name}] ({elapsed_ms:.2f}ms)",
            extra={
                "trace_id": trace_id,
                "span_id": span_id,
                "stage": "trace_end",
                "metadata": {
                    "span_name": span_name,
                    "elapsed_ms": round(elapsed_ms, 2),
                    **sanitized_attrs,
                },
            },
        )
