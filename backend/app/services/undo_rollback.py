"""Transactional patch rollback stack with undo logging and state recovery.

Provides a LIFO undo/redo stack for applied refactoring plans,
with logging and state recovery capabilities for multi-turn
conversational pair programming sessions.
"""
import uuid
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path


class UndoEntry:
    """A single undo/redo entry representing a plan application state."""

    def __init__(
        self,
        entry_id: Optional[str],
        plan_id: str,
        before_code: str,
        after_code: str,
        timestamp: Optional[str] = None,
    ):
        self.entry_id = entry_id or str(uuid.uuid4())
        self.plan_id = plan_id
        self.before_code = before_code
        self.after_code = after_code
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize undo entry to dict."""
        return {
            "entry_id": self.entry_id,
            "plan_id": self.plan_id,
            "before_code": self.before_code,
            "after_code": self.after_code,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UndoEntry":
        """Deserialize undo entry from dict."""
        return cls(
            entry_id=data.get("entry_id"),
            plan_id=data["plan_id"],
            before_code=data["before_code"],
            after_code=data["after_code"],
            timestamp=data.get("timestamp"),
        )


class UndoRollbackStack:
    """LIFO undo/redo stack for applied refactoring plans.

    Supports:
    - Undo: revert the most recent plan application
    - Redo: re-apply the most recently undone plan
    - Logging: each entry is logged with plan_id and timestamps
    - State recovery: restore code to any previous state
    - Persistence: entries can be serialized/desisted for storage
    """

    def __init__(self):
        self._undo_stack: List[UndoEntry] = []
        self._redo_stack: List[UndoEntry] = []
        self._entry_count = 0

    def push(self, entry: UndoEntry) -> None:
        """Push an undo entry, clearing the redo stack."""
        self._undo_stack.append(entry)
        self._redo_stack.clear()
        self._entry_count += 1

    def pop_undo(self) -> Optional[UndoEntry]:
        """Pop the most recent undo entry, moving it to redo stack."""
        if not self._undo_stack:
            return None
        entry = self._undo_stack.pop()
        self._redo_stack.append(entry)
        return entry

    def pop_redo(self) -> Optional[UndoEntry]:
        """Pop the most recent redo entry, moving it to undo stack."""
        if not self._redo_stack:
            return None
        entry = self._redo_stack.pop()
        self._undo_stack.append(entry)
        return entry

    def peek_undo(self) -> Optional[UndoEntry]:
        """View the most recent undo entry without popping."""
        if not self._undo_stack:
            return None
        return self._undo_stack[-1]

    def peek_redo(self) -> Optional[UndoEntry]:
        """View the most recent redo entry without popping."""
        if not self._redo_stack:
            return None
        return self._redo_stack[-1]

    def can_undo(self) -> bool:
        """Check if undo is available."""
        return len(self._undo_stack) > 0

    def can_redo(self) -> bool:
        """Check if redo is available."""
        return len(self._redo_stack) > 0

    def size(self) -> int:
        """Return total number of undo entries."""
        return len(self._undo_stack)

    def clear(self) -> None:
        """Clear both stacks."""
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._entry_count = 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the entire stack state to dict."""
        return {
            "undo_stack": [e.to_dict() for e in self._undo_stack],
            "redo_stack": [e.to_dict() for e in self._redo_stack],
            "entry_count": self._entry_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UndoRollbackStack":
        """Deserialize stack state from dict."""
        stack = cls()
        for e_data in data.get("undo_stack", []):
            stack.push(UndoEntry.from_dict(e_data))
        for e_data in data.get("redo_stack", []):
            # Push to redo by using the internal method, but since
            # push clears redo, we add directly
            entry = UndoEntry.from_dict(e_data)
            stack._redo_stack.append(entry)
        stack._entry_count = data.get("entry_count", 0)
        return stack

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the stack state."""
        return {
            "undo_count": len(self._undo_stack),
            "redo_count": len(self._redo_stack),
            "entry_count": self._entry_count,
            "can_undo": self.can_undo(),
            "can_redo": self.can_redo(),
        }
