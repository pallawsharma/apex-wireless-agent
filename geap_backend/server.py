"""Apex Wireless Hybrid Microservice: GEAP Multi-Agent Backend for GECX Telephony.

Exposes dual endpoints:
1. POST /api/dispatch : OpenAPI 3.0 Tool endpoint for GECX Agent Studio
2. POST /webhook/cx   : Native Dialogflow CX Fulfillment Webhook endpoint
3. GET  /healthz      : Service health check
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Ensure project root is in sys.path
BACKEND_ROOT = Path(__file__).resolve().parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Configure Gemini Enterprise Agent Platform (Vertex AI) if no direct API key is set
if "GOOGLE_API_KEY" not in os.environ and "GEMINI_API_KEY" not in os.environ:
    os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "1")
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "354292934503")
    os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-central1")

from fastapi import FastAPI, Request, Depends, HTTPException, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn

from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from agent import root_agent
from handlers.openapi_handler import OpenAPIHandler, DispatchRequest, DispatchResponse
from handlers.cx_webhook_handler import CXWebhookHandler

# Security & Authorization configuration
security = HTTPBearer(auto_error=False)
EXPECTED_AUTH_TOKEN = os.environ.get("APEX_AUTH_TOKEN", "apex-enterprise-secret-token-2026")

async def verify_authorization(credentials: Optional[HTTPAuthorizationCredentials] = Security(security), request: Request = None):
    """Enforces Enterprise Token / Service Account authentication for GECX -> GEAP calls.
    
    Accepts:
    1. 'Authorization: Bearer <APEX_AUTH_TOKEN>'
    2. 'X-Apex-Secret: <APEX_AUTH_TOKEN>'
    3. Bypass in local development when APEX_ENFORCE_AUTH=0.
    """
    enforce_auth = os.environ.get("APEX_ENFORCE_AUTH", "0") == "1"
    if not enforce_auth:
        return True

    # Check Bearer token
    if credentials and credentials.credentials == EXPECTED_AUTH_TOKEN:
        return True

    # Check custom header
    if request:
        custom_header = request.headers.get("X-Apex-Secret")
        if custom_header and custom_header == EXPECTED_AUTH_TOKEN:
            return True

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized: Valid Enterprise Bearer Token or X-Apex-Secret header required.",
        headers={"WWW-Authenticate": "Bearer"},
    )

app = FastAPI(
    title="Apex Wireless Hybrid GEAP Backend",
    description="Multi-Agent Microservice serving GECX Telephony Frontend via OpenAPI Tools & CX Webhooks",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from observability import logger, trace_span, redact_pii
from guardrails import validate_input_guardrail, validate_output_guardrail
from memory_manager import schedule_async_memory_save

session_service = InMemorySessionService()
runner = Runner(
    agent=root_agent,
    app_name="apex_wireless_hybrid",
    session_service=session_service,
)

openapi_handler = OpenAPIHandler(runner=runner, session_service=session_service)
cx_handler = CXWebhookHandler(runner=runner, session_service=session_service)


@app.get("/healthz")
async def health_check():
    return {
        "status": "healthy",
        "service": "apex-wireless-geap-backend",
        "version": "1.0.0",
        "auth_enforced": os.environ.get("APEX_ENFORCE_AUTH", "0") == "1",
        "observability": "OpenTelemetry + Structured JSON Logs",
        "guardrails": "Prompt Injection & Leakage Prevention Active",
    }


@app.post("/api/dispatch", response_model=DispatchResponse, dependencies=[Depends(verify_authorization)])
async def api_dispatch(req: DispatchRequest):
    """OpenAPI Tool endpoint for GECX Agent Studio to delegate multi-agent tasks."""
    session_id = req.session_id or "hybrid_session_default"

    with trace_span("api_dispatch", attributes={"session_id": session_id, "query": req.query}):
        # Input Guardrail Check
        input_check = validate_input_guardrail(req.query, session_id=session_id)
        if not input_check["passed"]:
            return DispatchResponse(
                status="blocked_by_guardrail",
                reply_text=input_check["safe_fallback"],
                active_agent="guardrail_policy",
                tool_calls_executed=[],
                updated_session_state={},
            )

        # Execute multi-agent reasoning
        response = await openapi_handler.handle_dispatch(req)

        # Output Guardrail Check & Sanitation
        output_check = validate_output_guardrail(response.reply_text, session_id=session_id)
        response.reply_text = output_check["sanitized_response"]

        # Async Memory Consolidation (Background non-blocking task)
        schedule_async_memory_save(
            session_id=session_id,
            user_query=req.query,
            agent_response=response.reply_text,
            parameters=response.updated_session_state,
        )

        return response


@app.post("/webhook/cx", dependencies=[Depends(verify_authorization)])
async def cx_webhook(request: Request):
    """Dialogflow CX Fulfillment Webhook endpoint."""
    payload = await request.json()
    session_id = payload.get("sessionInfo", {}).get("session", "unknown_cx_session")

    with trace_span("cx_webhook", attributes={"session_id": session_id}):
        response = await cx_handler.handle_webhook(payload)

        # Extract text reply for async background memory consolidation
        messages = response.get("fulfillment_response", {}).get("messages", [])
        reply_text = ""
        if messages and "text" in messages[0]:
            reply_text = " ".join(messages[0]["text"].get("text", []))

        schedule_async_memory_save(
            session_id=session_id,
            user_query="[CX_WEBHOOK_EVENT]",
            agent_response=reply_text,
            parameters=response.get("sessionInfo", {}).get("parameters", {}),
        )

        return response


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting Apex Wireless Hybrid GEAP Backend on http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
