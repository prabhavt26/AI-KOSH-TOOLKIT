from sqlalchemy import Column, String, ForeignKey, Enum, TIMESTAMP, func, Index, text, event, DDL
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from datetime import datetime, timezone
from app.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    __table_args__ = (
        Index('idx_audit_logs_event_type', 'event_type'),
    )

    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("uuid_generate_v4()"))
    assessment_id = Column(UUID(as_uuid=True), ForeignKey("assessments.assessment_id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(100), nullable=False)
    event_timestamp = Column(TIMESTAMP(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), server_default=func.now(), index=True)

    component = Column(String(100), nullable=True)
    event_detail = Column(JSONB, default=dict, nullable=False)
    severity = Column(String(20), default="INFO", server_default=text("'INFO'"), nullable=False)


    # Relationships
    assessment = relationship("Assessment", back_populates="audit_logs")

# Auto-register append-only rule when tables are created via Base.metadata.create_all (e.g. in tests)
event.listen(
    AuditLog.__table__,
    "after_create",
    DDL("CREATE RULE no_delete_audit AS ON DELETE TO audit_logs DO INSTEAD NOTHING;")
)
