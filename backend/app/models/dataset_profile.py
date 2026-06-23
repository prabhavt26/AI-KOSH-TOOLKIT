from sqlalchemy import Column, String, ForeignKey, TIMESTAMP, func, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from app.database import Base

class DatasetProfile(Base):
    __tablename__ = "dataset_profiles"

    profile_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("uuid_generate_v4()"))
    assessment_id = Column(UUID(as_uuid=True), ForeignKey("assessments.assessment_id", ondelete="CASCADE"), nullable=False, index=True)
    profile_json = Column(JSONB, nullable=False)
    profiled_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    profiler_version = Column(String(20), default="1.0.0", server_default=text("'1.0.0'"), nullable=False)

    # Relationships
    assessment = relationship("Assessment", back_populates="profile")
