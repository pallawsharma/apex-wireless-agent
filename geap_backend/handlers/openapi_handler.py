"""OpenAPI Tool Handler for GECX -> GEAP Hybrid Delegation.

Handles REST payloads sent by GECX Agent Studio OpenAPI tools.
"""

from typing import Any, Dict, List, Optional
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types
from pydantic import BaseModel


class DispatchRequest(BaseModel):
    query: str
    session_id: Optional[str] = "hybrid_session_default"
    user_id: Optional[str] = "alex_rivera"
    caller_phone_number: Optional[str] = "+14155550199"
    customer_name: Optional[str] = "Alex Rivera"
    account_id: Optional[str] = "ACC-1001"


class DispatchResponse(BaseModel):
    status: str
    reply_text: str
    active_agent: str
    tool_calls_executed: List[str]
    updated_session_state: Dict[str, Any]


class OpenAPIHandler:
    def __init__(self, runner: Runner, session_service: InMemorySessionService):
        self.runner = runner
        self.session_service = session_service
        self.initialized_sessions = set()

    async def handle_dispatch(self, req: DispatchRequest) -> DispatchResponse:
        session_id = req.session_id or "hybrid_session_default"
        user_id = req.user_id or "alex_rivera"

        if session_id not in self.initialized_sessions:
            await self.session_service.create_session(
                app_name="apex_wireless_hybrid",
                user_id=user_id,
                session_id=session_id,
                state={
                    "customer_name": req.customer_name or "Valued Customer",
                    "caller_phone_number": req.caller_phone_number or "",
                    "account_id": req.account_id or "",
                    "active_lines_count": 2,
                    "current_plan": "Unlimited Plus",
                    "primary_device": "iPhone 15 Pro",
                    "is_authenticated": True,
                },
            )
            self.initialized_sessions.add(session_id)

        msg_content = types.Content(
            role="user",
            parts=[types.Part.from_text(text=req.query)],
        )

        response_chunks = []
        author = "steering_agent"
        tools_called = []

        async for event in self.runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=msg_content,
        ):
            if event.author:
                author = event.author

            # Track tool calls if available
            if event.content and event.content.parts:
                for part in event.content.parts:
                    fn_call = getattr(part, "function_call", None)
                    if fn_call:
                        tools_called.append(getattr(fn_call, "name", str(fn_call)))
                    text_val = getattr(part, "text", None)
                    if text_val:
                        response_chunks.append(text_val)

        full_reply = "".join(response_chunks).strip() or "I have processed your request."

        # Fetch current session state safely
        current_state = {}
        try:
          session = await self.session_service.get_session(
              app_name="apex_wireless_hybrid",
              user_id=user_id,
              session_id=session_id,
          )
          if session and hasattr(session, "state"):
            current_state = session.state
        except Exception:
          pass

        return DispatchResponse(
            status="success",
            reply_text=full_reply,
            active_agent=author,
            tool_calls_executed=tools_called,
            updated_session_state=current_state,
        )
