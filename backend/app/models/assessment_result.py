from sqlalchemy import Column, Numeric, Integer, String, ForeignKey, Enum, Boolean, TIMESTAMP, func, CheckConstraint, Index, text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.database import Base

class AssessmentResult(Base):
    __tablename__ = "assessment_results"

    __table_args__ = (
        CheckConstraint('prs >= 0 AND prs <= 100', name='chk_assessment_results_prs'),
        Index('idx_assessment_results_release_classification', 'release_classification'),
        Index('idx_assessment_results_cqi', text('cqi DESC')),
    )

    result_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("uuid_generate_v4()"))
    assessment_id = Column(UUID(as_uuid=True), ForeignKey("assessments.assessment_id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    cqi = Column(Numeric(precision=5, scale=1), nullable=False)
    cqi_band = Column(String(20), nullable=False)
    total_domain_score = Column(Integer, nullable=False)
    max_possible_score = Column(Integer, nullable=False)
    cqi_formula_trace = Column(String(100), nullable=True)
    
    prs = Column(Integer, nullable=False)
    prs_band = Column(String(20), nullable=False)
    prs_baseline_risk = Column(Numeric(precision=6, scale=2), nullable=True)
    prs_sensitivity_multiplier = Column(Numeric(precision=4, scale=2), nullable=True)
    prs_computation_trace = Column(String, nullable=True)
    
    release_classification = Column(Enum("Open", "Controlled", "Restricted", name="release_class"), nullable=False)
    classification_justification = Column(String, nullable=True)
    policy_override_applied = Column(Boolean, default=False, server_default=text("false"), nullable=False)
    
    report_json_url = Column(String(500), nullable=True)
    report_html_url = Column(String(500), nullable=True)
    report_pdf_url = Column(String(500), nullable=True)
    
    computed_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    assessment = relationship("Assessment", back_populates="result")

