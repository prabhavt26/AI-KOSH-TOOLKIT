from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog
from typing import Dict, Any, Literal
from uuid import UUID

class AuditLogger:
    @staticmethod
    async def log_event(
        db: AsyncSession,
        assessment_id: UUID,
        event_type: str,
        event_detail: Dict[str, Any],
        component: str,
        severity: Literal["INFO", "WARNING", "ERROR"] = "INFO"
    ) -> AuditLog:
        """Inserts a structured audit log event into the database."""
        log = AuditLog(
            assessment_id=assessment_id,
            event_type=event_type,
            event_detail=event_detail,
            component=component,
            severity=severity
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)
        return log

    @staticmethod
    def log_event_sync(
        db,
        assessment_id: UUID,
        event_type: str,
        event_detail: Dict[str, Any],
        component: str,
        severity: Literal["INFO", "WARNING", "ERROR"] = "INFO"
    ) -> AuditLog:
        """Inserts a structured audit log event into the database synchronously."""
        log = AuditLog(
            assessment_id=assessment_id,
            event_type=event_type,
            event_detail=event_detail,
            component=component,
            severity=severity
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

audit_logger = AuditLogger()

