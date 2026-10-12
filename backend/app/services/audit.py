"""Audit trail logger for refactor actions and security events."""
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any
from app.models.schemas import AuditLogEntry

class AuditService:
    def __init__(self):
        self._entries: List[AuditLogEntry] = []

    def log(self, action: str, user: str, details: Dict[str, Any]) -> AuditLogEntry:
        entry = AuditLogEntry(
            audit_id=f"audit-{uuid.uuid4().hex[:12]}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            action=action,
            user=user,
            details=details
        )
        self._entries.append(entry)
        return entry

    def list_entries(self, limit: int = 50) -> List[AuditLogEntry]:
        return list(reversed(self._entries[-limit:]))

audit_service = AuditService()
