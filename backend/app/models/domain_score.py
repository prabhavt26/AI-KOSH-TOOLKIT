from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum, TIMESTAMP, func, CheckConstraint, UniqueConstraint, Index, text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from app.database import Base

class DomainScore(Base):
    __tablename__ = "domain_scores"

    __table_args__ = (
        UniqueConstraint('assessment_id', 'domain_number', name='uq_domain_scores_assessment_domain'),
        CheckConstraint('domain_number >= 1 AND domain_number <= 15', name='chk_domain_scores_domain_number'),
        CheckConstraint('(score >= 1 AND score <= 4) OR score IS NULL', name='chk_domain_scores_score'),
        Index('idx_domain_scores_domain_number', 'domain_number'),
    )

    score_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("uuid_generate_v4()"))
    assessment_id = Column(UUID(as_uuid=True), ForeignKey("assessments.assessment_id", ondelete="CASCADE"), nullable=False, index=True)
    domain_number = Column(Integer, nullable=False)
    domain_name = Column(String(100), nullable=False)
    score = Column(Integer, nullable=True) # None/null if not applicable (e.g. Domain 11)
    not_applicable = Column(Boolean, default=False, server_default=text("false"), nullable=False)
    rationale = Column(String, nullable=True)
    evidence_items = Column(JSONB, default=list, nullable=False)
    gaps = Column(JSONB, default=list, nullable=False)
    confidence_level = Column(Enum("High", "Medium", "Low", name="confidence_level"), nullable=True)
    data_signals_count = Column(Integer, nullable=True)
    meta_signals_count = Column(Integer, nullable=True)
    inferred = Column(Boolean, default=False, server_default=text("false"), nullable=False)
    scored_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())



    # Relationships
    assessment = relationship("Assessment", back_populates="domain_scores")
