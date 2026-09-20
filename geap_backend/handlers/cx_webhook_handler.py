"""Dialogflow CX / CES Webhook Handler for Hybrid Architecture.

Converts Dialogflow CX WebhookRequest JSON into GEAP runner inputs and
returns a standard Dialogflow CX WebhookResponse.
"""

from typing import Any, Dict, List, Optional
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types


class CXWebhookHandler:
    def __init__(self, runner: Runner, session_service: InMemorySessionService):
        self.runner = runner
        self.session_service = session_service
        self.initialized_sessions = set()

    async def handle_webhook(self, cx_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Processes standard Dialogflow CX / CES WebhookRequest."""
        session_info = cx_payload.get("sessionInfo", {})
        session_path = session_info.get("session", "projects/default/sessions/hybrid_session_001")
        params = session_info.get("parameters", {})

        # Extract user input text from query, transcript, or tag
        user_text = (
            cx_payload.get("text")
            or params.get("user_query")
            or cx_payload.get("fulfillmentInfo", {}).get("tag")
            or "Hello"
        )

        user_id = params.get("account_id") or "alex_rivera"

        # Initialize session if first call
        if session_path not in self.initialized_sessions:
            await self.session_service.create_session(
                app_name="apex_wireless_hybrid",
                user_id=user_id,
                session_id=session_path,
                state={
                    "customer_name": params.get("customer_name", "Valued Customer"),
                    "caller_phone_number": params.get("caller_phone_number", "+14155550199"),
                    "account_id": params.get("account_id", "ACC-1001"),
                    "active_lines_count": params.get("active_lines_count", 2),
                    "current_plan": params.get("current_plan", "Unlimited Plus"),
                    "primary_device": params.get("primary_device", "iPhone 15 Pro"),
                    "is_authenticated": params.get("is_authenticated", True),
                },
            )
            self.initialized_sessions.add(session_path)

        msg_content = types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_text)],
        )

        response_chunks = []
        author = "steering_agent"

        async for event in self.runner.run_async(
            user_id=user_id,
            session_id=session_path,
            new_message=msg_content,
        ):
            if event.author:
                author = event.author
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        response_chunks.append(part.text)

        full_reply = "".join(response_chunks).strip() or "I have processed your request."

        # Fetch session state safely to pass back to Dialogflow CX session parameters
        updated_state = {}
        try:
          session = await self.session_service.get_session(
              app_name="apex_wireless_hybrid",
              user_id=user_id,
              session_id=session_path,
          )
          if session and hasattr(session, "state"):
            updated_state = session.state
        except Exception:
          pass

        # Merge updated session parameters back into Dialogflow CX
        returned_params = {**params}
        for k, v in updated_state.items():
            returned_params[k] = v
        returned_params["last_active_agent"] = author

        return {
            "fulfillmentResponse": {
                "messages": [
                    {
                        "text": {
                            "text": [full_reply]
                        }
                    }
                ]
            },
            "sessionInfo": {
                "parameters": returned_params
            }
        }
