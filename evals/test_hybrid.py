"""Automated End-to-End Evaluation for Architecture 3 (Hybrid GECX + GEAP).

Simulates GECX Telephony Edge invoking the GEAP Multi-Agent Backend over:
1. OpenAPI Tool Dispatch (/api/dispatch)
2. Native Dialogflow CX Fulfillment Webhook (/webhook/cx)
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Setup paths
HYBRID_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = HYBRID_ROOT / "geap_backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Configure Vertex AI
if "GOOGLE_API_KEY" not in os.environ and "GEMINI_API_KEY" not in os.environ:
    os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "1")
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "354292934503")
    os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-central1")

from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from agent import root_agent
from handlers.openapi_handler import OpenAPIHandler, DispatchRequest
from handlers.cx_webhook_handler import CXWebhookHandler

TEST_SCENARIOS = [
    {
        "turn": 1,
        "mode": "openapi",
        "description": "Sales Inquiry: Google Pixel 9 Pro Fold pricing & family discounts",
        "query": "How much is the Google Pixel 9 Pro Fold and what are your family plan rates?",
        "expected_agent": "sales_agent",
        "expected_keywords": ["1,799", "1799", "one thousand seven hundred", "35", "thirty-five"],
    },
    {
        "turn": 2,
        "mode": "openapi",
        "description": "Store Reservation: Pixel 9 Pro pickup near 94105 for Alex Rivera",
        "query": "Can I reserve a Pixel 9 Pro for store pickup near 94105? My name is Alex Rivera.",
        "expected_agent": "sales_agent",
        "expected_keywords": ["RES-", "48 hours", "Market Street", "Downtown", "reserved"],
    },
    {
        "turn": 3,
        "mode": "openapi",
        "description": "Support Diagnostics: Slow data speeds on iPhone 15 Pro",
        "query": "My data connection has been really slow today. Can you run diagnostics on my line?",
        "expected_agent": "support_agent",
        "expected_keywords": ["diagnostics", "Airplane mode", "eSIM", "5G", "bars", "signal"],
    },
    {
        "turn": 4,
        "mode": "openapi",
        "description": "Returns & Restocking: Return opened Pixel 9 Pro at SF store",
        "query": "I bought a Pixel 9 Pro last week, opened it, and want to return it at your SF store. What is the fee?",
        "expected_agent": "support_agent",
        "expected_keywords": ["35", "thirty-five", "restocking", "RMA-", "refund", "964", "nine hundred sixty-four"],
    },
    {
        "turn": 5,
        "mode": "cx_webhook",
        "description": "CX Fulfillment Webhook: Itemized bill explanation and due date",
        "query": "Why is my current bill $85.50 and when is it due?",
        "expected_keywords": ["85.50", "eighty-five", "October 1st", "October first", "AutoPay", "due"],
    },
]


async def run_hybrid_eval():
    print("=" * 80)
    print("STARTING HYBRID ARCHITECTURE EVALUATION (GECX Voice Edge + GEAP Multi-Agent)")
    print("=" * 80)

    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent,
        app_name="apex_wireless_hybrid",
        session_service=session_service,
    )

    openapi_handler = OpenAPIHandler(runner=runner, session_service=session_service)
    cx_handler = CXWebhookHandler(runner=runner, session_service=session_service)

    session_id = "projects/354292934503/locations/us/apps/hybrid-app/sessions/test-call-001"
    passed = 0

    for scenario in TEST_SCENARIOS:
        turn = scenario["turn"]
        print(f"\n[Turn {turn}] Mode: {scenario['mode'].upper()} | {scenario['description']}")
        print(f"GECX Inbound Speech: \"{scenario['query']}\"")

        if scenario["mode"] == "openapi":
            req = DispatchRequest(
                query=scenario["query"],
                session_id=session_id,
                customer_name="Alex Rivera",
                caller_phone_number="+14155550199",
                account_id="ACC-1001",
            )
            resp = await openapi_handler.handle_dispatch(req)
            reply = resp.reply_text
            agent = resp.active_agent
            tools = resp.tool_calls_executed

            print(f"GEAP Delegated Agent: [{agent}]")
            if tools:
                print(f"Python Tools Executed: {tools}")
            print(f"GEAP Reply for Telephony TTS: \"{reply}\"")

            # Assertions
            matched = any(kw.lower() in reply.lower() for kw in scenario["expected_keywords"])
            if matched:
                print(">>> STATUS: PASSED")
                passed += 1
            else:
                print(">>> STATUS: FAILED (keywords missing)")

        elif scenario["mode"] == "cx_webhook":
            cx_request = {
                "detectIntentResponseId": f"dir-{turn}",
                "text": scenario["query"],
                "sessionInfo": {
                    "session": session_id,
                    "parameters": {
                        "customer_name": "Alex Rivera",
                        "caller_phone_number": "+14155550199",
                        "account_id": "ACC-1001",
                        "user_query": scenario["query"],
                    },
                },
            }
            cx_resp = await cx_handler.handle_webhook(cx_request)
            messages = cx_resp.get("fulfillmentResponse", {}).get("messages", [])
            reply = messages[0]["text"]["text"][0] if messages else ""
            returned_params = cx_resp.get("sessionInfo", {}).get("parameters", {})

            print(f"CX Webhook Reply for Telephony TTS: \"{reply}\"")
            print(f"Updated CX Session Parameters: {list(returned_params.keys())}")

            matched = any(kw.lower() in reply.lower() for kw in scenario["expected_keywords"])
            if matched:
                print(">>> STATUS: PASSED")
                passed += 1
            else:
                print(">>> STATUS: FAILED (keywords missing)")

    print("\n" + "=" * 80)
    print(f"HYBRID EVALUATION COMPLETE: {passed}/{len(TEST_SCENARIOS)} Scenarios Passed ({passed/len(TEST_SCENARIOS)*100:.0f}%)")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_hybrid_eval())
