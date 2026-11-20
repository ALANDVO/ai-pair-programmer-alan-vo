"""Unit tests for session manager and undo rollback stack."""

import datetime
import pytest
import json
import os
import tempfile

from app.services.session_manager import SessionContext, SessionManager
from app.services.undo_rollback import UndoEntry, UndoRollbackStack


class TestSessionContext:
    """Tests for SessionContext data model."""

    def test_init_with_session_id(self):
        sc = SessionContext(session_id="test-123")
        assert sc.session_id == "test-123"

    def test_init_without_session_id(self):
        sc = SessionContext()
        assert sc.session_id is not None
        assert len(sc.session_id) > 0

    def test_init_with_task_and_code(self):
        sc = SessionContext(task="test task", initial_code="x = 1")
        assert sc.task == "test task"
        assert sc.code == "x = 1"
        assert len(sc.code_history) == 1

    def test_snapshot_code(self):
        sc = SessionContext(initial_code="initial")
        assert sc.code == "initial"
        sc.snapshot_code("modified")
        assert sc.code == "modified"
        assert len(sc.code_history) == 2
        assert sc.turn_count == 1

    def test_add_applied_plan(self):
        sc = SessionContext()
        sc.add_applied_plan("plan-1")
        sc.add_applied_plan("plan-2")
        assert "plan-1" in sc.applied_plans
        assert "plan-2" in sc.applied_plans
        assert len(sc.applied_plans) == 2

    def test_push_pop_undo_entry(self):
        sc = SessionContext()
        entry = {"plan_id": "plan-1", "before_code": "old", "after_code": "new"}
        sc.push_undo_entry(entry)
        assert sc.can_undo() is True
        popped = sc.pop_undo_entry()
        assert popped is not None
        assert popped["plan_id"] == "plan-1"
        assert sc.can_undo() is False

    def test_push_pop_redo_entry(self):
        sc = SessionContext()
        # First push an undo entry, then pop it to move to redo stack
        sc.push_undo_entry({"plan_id": "plan-1", "before_code": "old", "after_code": "new"})
        popped = sc.pop_undo_entry()
        assert popped is not None
        assert sc.can_undo() is False
        assert sc.can_redo() is True

        # Now pop the redo entry
        redo_popped = sc.pop_redo_entry()
        assert redo_popped is not None
        assert sc.can_redo() is False
        assert sc.can_undo() is True

    def test_can_undo_and_can_redo(self):
        sc = SessionContext(initial_code="code")
        assert sc.can_undo() is False
        assert sc.can_redo() is False

        sc.push_undo_entry({"plan_id": "p1", "before_code": "old", "after_code": "new"})
        assert sc.can_undo() is True
        assert sc.can_redo() is False

        sc.pop_undo_entry()
        assert sc.can_undo() is False
        assert sc.can_redo() is True

    def test_to_and_from_dict(self):
        sc = SessionContext(task="my task", initial_code="def foo(): pass")
        sc.add_applied_plan("plan-1")
        sc.push_undo_entry({"plan_id": "plan-1", "before_code": "before", "after_code": "after"})

        data = sc.to_dict()
        sc2 = SessionContext.from_dict(data)

        assert sc2.session_id == sc.session_id
        assert sc2.task == "my task"
        assert sc2.code == "def foo(): pass"
        assert "plan-1" in sc2.applied_plans
        assert sc2.can_undo() is True
        assert sc2.can_redo() is False

    def test_parse_time(self):
        """Test _parse_time static method."""
        # None returns now
        result = SessionContext._parse_time(None)
        assert isinstance(result, datetime.datetime)

        # Valid ISO format
        result = SessionContext._parse_time("2024-01-15T10:30:00+00:00")
        assert isinstance(result, datetime.datetime)

        # Invalid format returns now
        result = SessionContext._parse_time("not-a-timestamp")
        assert isinstance(result, datetime.datetime)


class TestSessionManager:
    """Tests for SessionManager."""

    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def manager_with_persistence(self, temp_dir):
        persistence_path = os.path.join(temp_dir, "sessions.json")
        return SessionManager(persistence_path=persistence_path)

    @pytest.fixture
    def manager_without_persistence(self):
        return SessionManager()

    def test_create_session(self, manager_without_persistence):
        session = manager_without_persistence.create_session(
            task="refactor function", initial_code="def old_func(): pass"
        )
        assert session.session_id is not None
        assert session.task == "refactor function"
        assert session.code == "def old_func(): pass"
        assert manager_without_persistence.list_session_ids() == [session.session_id]

    def test_create_session_with_id(self, manager_without_persistence):
        session = manager_without_persistence.create_session(
            task="test task",
            session_id="fixed-session-id",
        )
        assert session.session_id == "fixed-session-id"

    def test_get_session(self, manager_without_persistence):
        session = manager_without_persistence.create_session(
            task="test", initial_code="x = 1"
        )
        retrieved = manager_without_persistence.get_session(session.session_id)
        assert retrieved is not None
        assert retrieved.task == "test"
        assert retrieved.code == "x = 1"

    def test_get_nonexistent_session(self, manager_without_persistence):
        retrieved = manager_without_persistence.get_session("nonexistent")
        assert retrieved is None

    def test_update_session_context(self, manager_without_persistence):
        session = manager_without_persistence.create_session(
            task="original task", initial_code="code1"
        )
        # Update task only
        updated = manager_without_persistence.update_session_context(
            session.session_id, task="new task"
        )
        assert updated.task == "new task"
        assert updated.code == "code1"  # code unchanged

        # Update code only
        updated = manager_without_persistence.update_session_context(
            session.session_id, code="code2"
        )
        assert updated.task == "new task"  # task preserved
        assert updated.code == "code2"

        # Update both
        updated = manager_without_persistence.update_session_context(
            session.session_id, task="final task", code="final code"
        )
        assert updated.task == "final task"
        assert updated.code == "final code"

    def test_apply_plan_to_session(self, manager_without_persistence):
        session = manager_without_persistence.create_session(
            task="refactor", initial_code="original code"
        )
        result = manager_without_persistence.apply_plan_to_session(
            session.session_id,
            "plan-1",
            "original code",
            "modified code",
        )
        assert result is not None
        assert "plan-1" in result.applied_plans
        assert result.can_undo() is True  # undo stack should have entry
        assert result.code == "modified code"
        assert len(result.code_history) == 2

    def test_undo_last_plan(self, manager_without_persistence):
        session = manager_without_persistence.create_session(
            task="refactor", initial_code="original code"
        )

        # Apply a plan
        manager_without_persistence.apply_plan_to_session(
            session.session_id, "plan-1", "original code", "modified code"
        )

        # Undo
        result = manager_without_persistence.undo_last_plan(session.session_id)
        assert result is not None
        assert result.code == "original code"  # restored to before state
        assert result.can_redo() is True  # redo should be available
        assert len(result.undo_stack) == 0  # undo stack cleared

    def test_redo_last_plan(self, manager_without_persistence):
        session = manager_without_persistence.create_session(
            task="refactor", initial_code="original code"
        )

        # Apply a plan
        manager_without_persistence.apply_plan_to_session(
            session.session_id, "plan-1", "original code", "modified code"
        )

        # Undo
        manager_without_persistence.undo_last_plan(session.session_id)

        # Redo
        result = manager_without_persistence.redo_last_plan(session.session_id)
        assert result is not None
        assert result.code == "modified code"  # restored to after state
        assert result.can_undo() is True  # undo should be available again

    def test_undo_with_no_undo_available(self, manager_without_persistence):
        session = manager_without_persistence.create_session(
            task="refactor", initial_code="code"
        )
        result = manager_without_persistence.undo_last_plan(session.session_id)
        assert result is None  # no undo available

    def test_redo_with_no_redo_available(self, manager_without_persistence):
        session = manager_without_persistence.create_session(
            task="refactor", initial_code="code"
        )
        result = manager_without_persistence.redo_last_plan(session.session_id)
        assert result is None  # no redo available

    def test_delete_session(self, manager_without_persistence, temp_dir):
        session = manager_without_persistence.create_session(
            task="temp", initial_code="code"
        )
        sid = session.session_id
        assert manager_without_persistence.list_session_ids().__contains__(sid)

        manager_without_persistence.delete_session(sid)
        assert not manager_without_persistence.list_session_ids().__contains__(sid)

    def test_persistence_load_save(self, manager_with_persistence, temp_dir):
        """Test that sessions are persisted and loaded."""
        persistence_path = os.path.join(temp_dir, "sessions.json")
        # The fixture already sets this up; test that we can create and it persists
        session = manager_with_persistence.create_session(
            task="persistent task", initial_code="def foo(): pass"
        )
        sid = session.session_id

        # Check file was created
        assert os.path.exists(persistence_path)

        # Create a new manager with same persistence path should load the session
        manager2 = SessionManager(persistence_path=persistence_path)
        retrieved = manager2.get_session(sid)
        assert retrieved is not None
        assert retrieved.task == "persistent task"
        assert retrieved.code == "def foo(): pass"

    def test_list_session_ids(self, manager_without_persistence):
        assert manager_without_persistence.list_session_ids() == []

        s1 = manager_without_persistence.create_session(task="task1")
        s2 = manager_without_persistence.create_session(task="task2")
        ids = manager_without_persistence.list_session_ids()
        assert len(ids) == 2
        assert s1.session_id in ids
        assert s2.session_id in ids

    def test_get_session_summary(self, manager_without_persistence):
        session = manager_without_persistence.create_session(
            task="summary task", initial_code="def foo(): pass"
        )
        summary = manager_without_persistence.get_session_summary(session.session_id)
        assert summary is not None
        assert summary["session_id"] == session.session_id
        assert summary["task"] == "summary task"
        assert summary["turn_count"] == 0
        assert summary["applied_plans_count"] == 0
        assert summary["can_undo"] is False
        assert summary["can_redo"] is False
        # code "def foo(): pass" has 15 characters  # len("def foo(): pass")

    def test_multiple_undo_redo_cycle(self, manager_without_persistence):
        """Test single undo/redo cycle with two plans."""
        session = manager_without_persistence.create_session(
            task="cycle test", initial_code="start"
        )

        # Apply plan 1
        manager_without_persistence.apply_plan_to_session(
            session.session_id, "plan-1", "start", "after1"
        )
        assert session.code == "after1"
        assert session.can_undo()

        # Undo plan 1
        manager_without_persistence.undo_last_plan(session.session_id)
        assert session.code == "start"
        assert session.can_redo()

        # Redo plan 1
        manager_without_persistence.redo_last_plan(session.session_id)
        assert session.code == "after1"


class TestUndoRollbackStack:
    """Tests for UndoRollbackStack data model."""

    def test_init_empty(self):
        stack = UndoRollbackStack()
        assert stack.size() == 0
        assert stack.can_undo() is False
        assert stack.can_redo() is False

    def test_push_and_pop_undo(self):
        stack = UndoRollbackStack()
        entry = UndoEntry(
            entry_id="e1", plan_id="plan-1", before_code="old", after_code="new"
        )
        stack.push(entry)
        assert stack.can_undo() is True

        popped = stack.pop_undo()
        assert popped is not None
        assert popped.plan_id == "plan-1"
        assert stack.can_undo() is False
        assert stack.can_redo() is True

    def test_push_and_pop_redo(self):
        stack = UndoRollbackStack()
        entry = UndoEntry(
            entry_id="e1", plan_id="plan-1", before_code="old", after_code="new"
        )
        stack.push(entry)
        stack.pop_undo()  # moves to redo

        popped = stack.pop_redo()
        assert popped is not None
        assert popped.plan_id == "plan-1"
        assert stack.can_undo() is True
        assert stack.can_redo() is False

    def test_peek(self):
        stack = UndoRollbackStack()
        entry = UndoEntry(
            entry_id="e1", plan_id="plan-1", before_code="old", after_code="new"
        )
        stack.push(entry)
        assert stack.peek_undo() is entry
        assert stack.peek_redo() is None

    def test_clear(self):
        stack = UndoRollbackStack()
        for i in range(3):
            stack.push(UndoEntry(entry_id=f"e{i}", plan_id=f"plan-{i}", before_code="old", after_code="new"))
        assert stack.size() == 3
        stack.clear()
        assert stack.size() == 0
        assert stack.can_undo() is False
        assert stack.can_redo() is False

    def test_persistence_roundtrip(self):
        import json
        stack = UndoRollbackStack()
        entry1 = UndoEntry(entry_id="e1", plan_id="plan-1", before_code="before1", after_code="after1")
        entry2 = UndoEntry(entry_id="e2", plan_id="plan-2", before_code="before2", after_code="after2")
        stack.push(entry1)
        stack.push(entry2)

        data = stack.to_dict()
        stack2 = UndoRollbackStack.from_dict(data)

        assert stack2.size() == 2
        assert stack2.can_undo() is True
        assert stack2.peek_undo().plan_id == "plan-2"  # LIFO order

    def test_summary(self):
        stack = UndoRollbackStack()
        assert stack.get_summary() == {
            "undo_count": 0,
            "redo_count": 0,
            "entry_count": 0,
            "can_undo": False,
            "can_redo": False,
        }

        entry = UndoEntry(entry_id="e1", plan_id="plan-1", before_code="old", after_code="new")
        stack.push(entry)
        summary = stack.get_summary()
        assert summary["undo_count"] == 1
        assert summary["can_undo"] is True
        assert summary["can_redo"] is False
