"""
Compatibility shims for Strands Agents SDK API differences.

This module provides fallbacks for:
- GraphBuilder (strands.multiagent)
- FileSessionManager (strands.session.file_session_manager)
- ToolContext (strands.types.tools)
- Basic multi-agent result types used in enhanced orchestrator

The goal is to keep the code importable and minimally functional when
the installed SDK version lacks certain modules.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, List, Callable

# ToolContext fallback
try:  # Prefer real ToolContext if available
    from strands.types.tools import ToolContext  # type: ignore
except Exception:  # pragma: no cover - fallback
    class ToolContext:  # minimal shape
        def __init__(self, invocation_state: Optional[Dict[str, Any]] = None) -> None:
            self.invocation_state = invocation_state or {}

        # Pydantic v2 compatibility: treat as arbitrary/any type in schemas
        @classmethod
        def __get_pydantic_core_schema__(cls, source_type, handler):  # type: ignore[override]
            try:
                from pydantic_core import core_schema
                return core_schema.any_schema()
            except Exception:  # Fallback if pydantic_core not available
                # Returning None will let Pydantic error; better to raise NotImplementedError
                raise NotImplementedError


# FileSessionManager fallback - Force use of compatibility implementation
# The native strands.session.file_session_manager.FileSessionManager doesn't have apply_management method
try:
    from strands.agent.conversation_manager import (
        SlidingWindowConversationManager,
    )  # type: ignore

    class FileSessionManager(SlidingWindowConversationManager):  # type: ignore
        def __init__(
            self,
            session_id: str,
            storage_dir: Optional[str] = None,
            session_directory: Optional[str] = None,
            max_history_length: int = 50,
            **_: Any,
        ) -> None:
            # Use sliding window with configured history length
            super().__init__(window_size=max_history_length)
            self.session_id = session_id
            # Keep for compatibility; not used by SlidingWindowConversationManager
            self.storage_dir = storage_dir or session_directory
            
        def apply_management(self, messages):
            """Apply conversation management - delegate to parent SlidingWindowConversationManager."""
            # Call parent's apply_management method
            super().apply_management(messages)

except Exception:
    class FileSessionManager:  # type: ignore
        def __init__(self, *args: Any, **kwargs: Any) -> None:  # minimal no-op
            pass
            
        def apply_management(self, messages) -> None:
            """Minimal no-op implementation of apply_management."""
            pass


# Multi-agent graph builder and types fallback
try:
    from strands.multiagent import GraphBuilder  # type: ignore
    from strands.multiagent.base import Status, NodeResult  # type: ignore
    from strands.multiagent import MultiAgentBase, MultiAgentResult  # type: ignore
except Exception:  # pragma: no cover - fallback
    # Minimal status enum
    class Status:
        COMPLETED = type("_S", (), {"value": "COMPLETED"})()
        FAILED = type("_S", (), {"value": "FAILED"})()

    class NodeResult:
        def __init__(self, result: Any = None) -> None:
            self.result = result

    class MultiAgentResult:
        def __init__(
            self,
            status: Status = Status.COMPLETED,
            results: Optional[Dict[str, NodeResult]] = None,
            execution_order: Optional[List[Any]] = None,
            total_execution_time: int = 0,
        ) -> None:
            self.status = status
            self.results = results or {}
            # Execution order expects objects with `.node_id`; keep simple ids
            self.execution_order = [type("_N", (), {"node_id": nid}) for nid in (execution_order or [])]
            self.total_execution_time = total_execution_time

    class MultiAgentBase:
        async def invoke_async(self, task: Any, **kwargs: Any) -> MultiAgentResult:  # pragma: no cover
            raise NotImplementedError()

    import inspect
    import asyncio

    class _GraphCompat:
        def __init__(self, entry_node: Any) -> None:
            self._entry = entry_node

        async def invoke_async(self, message: Any, *args: Any, **kwargs: Any) -> Any:
            """Invoke the single entry node and return plain text when possible.

            This is intentionally simple to keep tests running without full
            multi-agent support.
            """
            node = self._entry
            # Try common invocation patterns
            # Prefer async methods if available
            try:
                if hasattr(node, "invoke_async"):
                    res = await node.invoke_async(message)
                elif hasattr(node, "invoke"):
                    res = node.invoke(message)
                    if inspect.isawaitable(res):
                        res = await res
                elif callable(node):
                    res = node(message)
                    if inspect.isawaitable(res):
                        res = await res
                else:
                    res = str(node)
            except Exception as e:
                # Fallback for any invocation errors
                return f"Error processing message: {str(e)}"

            # Try to extract text content from AgentResult-like objects
            try:
                if hasattr(res, "message") and hasattr(res.message, "content"):
                    content = res.message.content
                    if content and len(content) > 0:
                        blk = content[0]
                        text = getattr(blk, "text", None)
                        if isinstance(text, str):
                            return text
                # Fallback to string
                return str(res)
            except Exception:
                return str(res)

    class GraphBuilder:
        """Very small graph builder that supports single-node graphs.

        Methods are no-ops except add_node/set_entry_point/build sufficient for
        the simplified orchestrator that adds one node.
        """

        def __init__(self) -> None:
            self._nodes: Dict[str, Any] = {}
            self._entry_id: Optional[str] = None

        def add_node(self, node: Any, node_id: str) -> None:
            self._nodes[node_id] = node

        def add_edge(self, *_: Any, **__: Any) -> None:
            # No-op in compat mode
            return None

        def set_entry_point(self, node_id: str) -> None:
            self._entry_id = node_id

        def set_max_node_executions(self, *_: Any, **__: Any) -> None:
            return None

        def set_execution_timeout(self, *_: Any, **__: Any) -> None:
            return None

        def set_node_timeout(self, *_: Any, **__: Any) -> None:
            return None

        def reset_on_revisit(self, *_: Any, **__: Any) -> None:
            return None

        def build(self) -> _GraphCompat:
            if not self._entry_id or self._entry_id not in self._nodes:
                # Fallback: pick any node
                entry = next(iter(self._nodes.values()), lambda x: x)
            else:
                entry = self._nodes[self._entry_id]
            return _GraphCompat(entry)
