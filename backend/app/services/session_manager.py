"""Session manager for multi-turn conversational pair programming sessions with context tracking.

Tracks session state across turns, including:
- Conversational context (code being discussed, refactoring goals)
- Applied patches with plan IDs
- User intent and task history
- Session metadata (start time, turn count, etc.)
"""
import datetime
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union


class SessionContext:
    """Context for a single conversational session, tracking state across turns."""

    def __init__(
        self,
        session_id: Optional[str] = None,
        task: Optional[str] = None,
        initial_code: Optional[str] = None,
    ):
        self.session_id = session_id or str(uuid.uuid4())
        self.task = task
        self.code_history: List[Tuple[str, str]] = []  # (timestamp, code_snapshot)
        self.applied_plans: List[str] = []  # plan_ids that were applied
        self.undo_stack: List[Dict[str, Any]] = []  # undo entries
        self.redo_stack: List[Dict[str, Any]] = []  # redo entries
        self.turn_count = 0
        self.created_at = datetime.now(timezone.utc)
        self.last_updated = self.created_at

        if initial_code is not None:
            self.code_history.append((self.last_updated.isoformat(), initial_code))
            self.code = initial_code

    def snapshot_code(self, code: str) -> None:
        """Record a code snapshot at the current turn."""
        self.last_updated = datetime.now(timezone.utc)
        self.code_history.append((self.last_updated.isoformat(), code))
        self.code = code
        self.turn_count += 1

    def add_applied_plan(self, plan_id: str) -> None:
        """Record that a plan was applied."""
        self.applied_plans.append(plan_id)

    def push_undo_entry(self, entry: Dict[str, Any]) -> None:
        """Push an undo entry (before state of an applied plan)."""
        self.undo_stack.append(entry)
        # Clear redo stack when new action is taken
        self.redo_stack.clear()

    def pop_undo_entry(self) -> Optional[Dict[str, Any]]:
        """Pop the most recent undo entry."""
        if not self.undo_stack:
            return None
        entry = self.undo_stack.pop()
        self.redo_stack.append(entry)
        return entry

    def push_redo_entry(self, entry: Dict[str, Any]) -> None:
        """Push a redo entry back onto the redo stack."""
        self.redo_stack.append(entry)

    def pop_redo_entry(self) -> Optional[Dict[str, Any]]:
        """Pop the most recent redo entry."""
        if not self.redo_stack:
            return None
        entry = self.redo_stack.pop()
        self.undo_stack.append(entry)
        return entry

    def can_undo(self) -> bool:
        """Check if undo is available."""
        return len(self.undo_stack) > 0

    def can_redo(self) -> bool:
        """Check if redo is available."""
        return len(self.redo_stack) > 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize session context to dict for storage/transport."""
        return {
            "session_id": self.session_id,
            "task": self.task,
            "code_history": self.code_history,
            "applied_plans": self.applied_plans,
            "undo_stack": self.undo_stack,
            "redo_stack": self.redo_stack,
            "turn_count": self.turn_count,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "code": self.code,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionContext":
        """Deserialize session context from dict."""
        sc = cls(
            session_id=data.get("session_id"),
            task=data.get("task"),
        )
        sc.code_history = data.get("code_history", [])
        sc.applied_plans = data.get("applied_plans", [])
        sc.undo_stack = data.get("undo_stack", [])
        sc.redo_stack = data.get("redo_stack", [])
        sc.turn_count = data.get("turn_count", 0)
        sc.created_at = cls._parse_time(data.get("created_at"))
        sc.last_updated = cls._parse_time(data.get("last_updated"))
        sc.code = data.get("code", "")
        return sc

    @staticmethod
    def _parse_time(s: Optional[str]) -> datetime:
        """Parse ISO format datetime string."""
        if s is None:
            return datetime.now(timezone.utc)
        try:
            return datetime.fromisoformat(s)
        except (ValueError, TypeError):
            return datetime.now(timezone.utc)


class SessionManager:
    """Manages conversational sessions with context tracking and undo/redo support."""

    def __init__(self, persistence_path: Optional[Union[str, Path]] = None):
        """Initialize session manager.

        Args:
            persistence_path: Optional path to JSON file for session persistence.
        """
        self.sessions: Dict[str, SessionContext] = {}
        self.persistence_path = Path(persistence_path) if persistence_path else None
        # If persistence path given, load existing sessions
        if self.persistence_path is not None and self.persistence_path.exists():
            self._load_sessions()

    def _load_sessions(self) -> None:
        """Load sessions from persistence file."""
        try:
            persistence = str(self.persistence_path)
            with open(persistence, "r") as f:
                data = json.load(f)
            for sid, sc_data in data.items():
                self.sessions[sid] = SessionContext.from_dict(sc_data)
        except (json.JSONDecodeError, IOError, KeyError):
            # Start fresh if file is corrupt or missing structure
            self.sessions = {}

    def _save_sessions(self) -> None:
        """Save all sessions to persistence file."""
        if self.persistence_path is None:
            return
        try:
            persistence = str(self.persistence_path)
            data = {}
            for sid, sc in self.sessions.items():
                data[sid] = sc.to_dict()
            with open(persistence, "w") as f:
                json.dump(data, f, indent=2)
        except IOError:
            # Non-fatal: sessions live in memory
            pass

    def create_session(
        self,
        task: str,
        initial_code: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> SessionContext:
        """Create a new conversational session."""
        session = SessionContext(
            session_id=session_id,
            task=task,
            initial_code=initial_code,
        )
        self.sessions[session.session_id] = session
        self._save_sessions()
        return session

    def get_session(self, session_id: str) -> Optional[SessionContext]:
        """Get a session by ID."""
        return self.sessions.get(session_id)

    def update_session_context(
        self,
        session_id: str,
        task: Optional[str] = None,
        code: Optional[str] = None,
    ) -> Optional[SessionContext]:
        """Update session task and/or code context."""
        session = self.sessions.get(session_id)
        if session is None:
            return None
        if task is not None:
            session.task = task
        if code is not None:
            session.snapshot_code(code)
        session.last_updated = datetime.now(timezone.utc)
        self._save_sessions()
        return session

    def apply_plan_to_session(
        self,
        session_id: str,
        plan_id: str,
        before_code: str,
        after_code: str,
    ) -> Optional[SessionContext]:
        """Record that a plan was applied and push undo entry.

        Args:
            session_id: The session to update
            plan_id: The plan that was applied
            before_code: Code before the plan was applied
            after_code: Code after the plan was applied

        Returns:
            Updated session context, or None if session not found
        """
        session = self.sessions.get(session_id)
        if session is None:
            return None

        session.add_applied_plan(plan_id)
        session.push_undo_entry({
            "plan_id": plan_id,
            "before_code": before_code,
            "after_code": after_code,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        session.snapshot_code(after_code)
        self._save_sessions()
        return session

    def undo_last_plan(self, session_id: str) -> Optional[SessionContext]:
        """Undo the most recently applied plan.

        Pops the undo stack to get the before-state, restores that code,
        and moves the current state to the redo stack.

        Returns:
            Updated session context, or None if session not found or no undo available
        """
        session = self.sessions.get(session_id)
        if session is None:
            return None

        if not session.can_undo():
            return None

        # Pop the most recent undo entry
        undo_entry = session.pop_undo_entry()

        # Restore before_code from the undo entry
        before_code = undo_entry["before_code"]
        # The original after_code is preserved in the undo entry
        original_after_code = undo_entry["after_code"]

        session.snapshot_code(before_code)

        # Push current state to redo stack with the original after_code
        session.push_redo_entry({
            "plan_id": undo_entry["plan_id"],
            "before_code": before_code,
            "after_code": original_after_code,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        session.last_updated = datetime.now(timezone.utc)
        self._save_sessions()
        return session

    def redo_last_plan(self, session_id: str) -> Optional[SessionContext]:
        """Redo the most recently undone plan.

        Pops the redo stack to get the redo entry, applies it,
        and moves the state to the undo stack.

        Returns:
            Updated session context, or None if session not found or no redo available
        """
        session = self.sessions.get(session_id)
        if session is None:
            return None

        if not session.can_redo():
            return None

        # Pop the most recent redo entry
        redo_entry = session.pop_redo_entry()

        # Apply the redo: restore after_code (this is the code state after the plan)
        after_code = redo_entry["after_code"]
        session.snapshot_code(after_code)

        # Push current state to undo stack with the code before the redo
        if session.code:
            session.push_undo_entry({
                "plan_id": redo_entry["plan_id"],
                "before_code": session.code,
                "after_code": after_code,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        session.last_updated = datetime.now(timezone.utc)
        self._save_sessions()
        return session

    def list_session_ids(self) -> List[str]:
        """List all session IDs."""
        return list(self.sessions.keys())

    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            self._save_sessions()
            return True
        return False

    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a summary of a session."""
        session = self.sessions.get(session_id)
        if session is None:
            return None
        return {
            "session_id": session.session_id,
            "task": session.task,
            "turn_count": session.turn_count,
            "applied_plans_count": len(session.applied_plans),
            "can_undo": session.can_undo(),
            "can_redo": session.can_redo(),
            "code_length": len(session.code) if session.code else 0,
        }
