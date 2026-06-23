from sqlalchemy import Column, String, Boolean, Enum, BIGINT, Integer, TIMESTAMP, func, text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.database import Base

class Assessment(Base):
    __tablename__ = "assessments"

    assessment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("uuid_generate_v4()"))
    dataset_id = Column(String(255), nullable=False, index=True)
    submitter_id = Column(String(255), nullable=True)
    submission_timestamp = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), index=True)
    completion_timestamp = Column(TIMESTAMP(timezone=True), nullable=True)
    status = Column(Enum("queued", "processing", "complete", "failed", name="assessment_status"), default="queued", server_default=text("'queued'"), nullable=False, index=True)
    toolkit_version = Column(String(20), default="1.0.0", server_default=text("'1.0.0'"), nullable=False)
    domain_11_applicable = Column(Boolean, default=True, server_default=text("true"), nullable=False)
    assessment_mode = Column(String(20), default="full", server_default=text("'full'"), nullable=False)
    file_format = Column(String(50), nullable=True)
    file_size_bytes = Column(BIGINT, nullable=True)
    file_sha256 = Column(String(64), nullable=True)
    s3_file_key = Column(String(500), nullable=True)
    error_message = Column(String, nullable=True)
    celery_task_id = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    domain_scores = relationship("DomainScore", back_populates="assessment", cascade="all, delete-orphan")
    result = relationship("AssessmentResult", uselist=False, back_populates="assessment", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="assessment", cascade="all, delete-orphan")
    metadata_form = relationship("DatasetMetadata", uselist=False, back_populates="assessment", cascade="all, delete-orphan")
    profile = relationship("DatasetProfile", uselist=False, back_populates="assessment", cascade="all, delete-orphan")

