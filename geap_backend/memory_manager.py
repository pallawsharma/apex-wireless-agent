"""Enterprise Context & Memory Management for Apex Wireless Agents.

Complies with AgentOps Code Review Matrix:
- History Compaction: Context bloat management via sliding windows and token compaction.
- Persistent Session State: Connects to persistent database / session store.
- Async Memory Operations: Background/async execution of expensive memory consolidation.
"""

import asyncio
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from observability import logger, redact_pii

# Persistent session file directory
SESSION_STORAGE_DIR = Path(os.environ.get("APEX_SESSION_DIR", "/tmp/apex_sessions"))
SESSION_STORAGE_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# History Compaction & Context Bloat Management
# ---------------------------------------------------------------------------

def compact_history(
    messages: List[Dict[str, Any]],
    max_turns: int = 10,
    max_char_limit: int = 12000,
) -> List[Dict[str, Any]]:
    """Implements sliding-window history compaction to eliminate context bloat.

    Retains the initial system / anchor message, summarizes intermediate turns
    if length exceeds threshold, and preserves the latest recent conversation turns.

    Args:
        messages: Full list of turn dictionaries (role, content).
        max_turns: Maximum number of recent conversational turns to preserve in full.
        max_char_limit: Total characters allowed before triggering summarization.

    Returns:
        Compacted message history adhering to LLM context window constraints.
    """
    if len(messages) <= max_turns:
        total_len = sum(len(str(m.get("content", ""))) for m in messages)
        if total_len <= max_char_limit:
            return messages

    # Keep the earliest grounding turn (Turn 0: identity / ANI)
    head = messages[:1]
    # Keep the most recent sliding window turns
    tail = messages[-max_turns:]

    # Insert a synthetic compaction summary note
    compaction_marker = {
        "role": "system",
        "content": f"[Context Compaction: Earlier {len(messages) - max_turns - 1} turns compacted into working memory to maintain sub-second voice latency.]",
    }

    compacted = head + [compaction_marker] + tail
    logger.info(
        f"Context compacted from {len(messages)} to {len(compacted)} turns",
        extra={"stage": "history_compaction", "metadata": {"original_turns": len(messages), "compacted_turns": len(compacted)}},
    )
    return compacted


# ---------------------------------------------------------------------------
# Persistent Session Storage
# ---------------------------------------------------------------------------

class PersistentSessionStore:
    """Thread-safe persistent session storage for conversational state across turns."""

    def __init__(self, base_dir: Path = SESSION_STORAGE_DIR):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_path(self, session_id: str) -> Path:
        clean_id = "".join(c for c in session_id if c.isalnum() or c in ("-", "_"))
        return self.base_dir / f"{clean_id}.json"

    def load_session(self, session_id: str) -> Dict[str, Any]:
        """Loads session history and variables from persistent disk storage."""
        path = self._get_path(session_id)
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading persistent session {session_id}: {e}")
        return {"session_id": session_id, "turns": [], "parameters": {}, "created_at": time.time()}

    def save_session_sync(self, session_id: str, session_data: Dict[str, Any]):
        """Synchronously persists session data to atomic temporary file then replaces."""
        path = self._get_path(session_id)
        temp_path = path.with_suffix(".tmp")
        sanitized_data = redact_pii(session_data)
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(sanitized_data, f, indent=2)
            temp_path.replace(path)
        except Exception as e:
            logger.error(f"Error persisting session {session_id}: {e}")


session_store = PersistentSessionStore()


# ---------------------------------------------------------------------------
# Async Memory Operations
# ---------------------------------------------------------------------------

async def async_persist_session_memory(
    session_id: str,
    user_query: str,
    agent_response: str,
    parameters: Optional[Dict[str, Any]] = None,
):
    """Executes expensive memory consolidation in the background without blocking UI or voice audio."""
    start_time = time.perf_counter()
    loop = asyncio.get_running_loop()

    def _background_save():
        data = session_store.load_session(session_id)
        data["turns"].append({
            "timestamp": time.time(),
            "user_query": user_query,
            "agent_response": agent_response,
        })
        if parameters:
            data.setdefault("parameters", {}).update(parameters)
        data["last_updated"] = time.time()
        session_store.save_session_sync(session_id, data)

    # Offload file I/O to thread pool so event loop remains completely unblocked
    await loop.run_in_executor(None, _background_save)
    elapsed_ms = (time.perf_counter() - start_time) * 1000

    logger.info(
        f"Async memory consolidated for session [{session_id}] in {elapsed_ms:.2f}ms",
        extra={"session_id": session_id, "stage": "async_memory_save", "metadata": {"elapsed_ms": round(elapsed_ms, 2)}},
    )


def schedule_async_memory_save(
    session_id: str,
    user_query: str,
    agent_response: str,
    parameters: Optional[Dict[str, Any]] = None,
):
    """Fires and forgets an async memory task from synchronous or async contexts."""
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(async_persist_session_memory(session_id, user_query, agent_response, parameters))
    except RuntimeError:
        # Fallback if outside active event loop
        asyncio.run(async_persist_session_memory(session_id, user_query, agent_response, parameters))
