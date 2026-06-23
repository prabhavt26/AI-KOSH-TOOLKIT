from sqlalchemy import Column, String, Integer, Date, Numeric, Boolean, ForeignKey, Enum, TIMESTAMP, func, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from app.database import Base

class DatasetMetadata(Base):
    __tablename__ = "dataset_metadata"

    metadata_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("uuid_generate_v4()"))
    assessment_id = Column(UUID(as_uuid=True), ForeignKey("assessments.assessment_id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_name = Column(String(500), nullable=False)
    dataset_version = Column(String(100), nullable=True)
    dataset_type = Column(String(50), nullable=True) # tabular/imaging/text/multimodal
    study_type = Column(String(100), nullable=True) # RCT/cohort/cross-sectional/registry
    target_population = Column(String, nullable=True)
    geographic_coverage = Column(String(255), nullable=True)
    
    age_range_min = Column(Integer, nullable=True)
    age_range_max = Column(Integer, nullable=True)
    sex_distribution = Column(String(50), nullable=True)
    num_sites = Column(Integer, nullable=True)
    
    collection_start_date = Column(Date, nullable=True)
    collection_end_date = Column(Date, nullable=True)
    
    annotation_methodology = Column(String, nullable=True)
    num_annotators = Column(Integer, nullable=True)
    irr_method = Column(String(100), nullable=True)
    irr_value = Column(Numeric(precision=5, scale=3), nullable=True)
    
    standards_used = Column(String(255), nullable=True)
    ethics_approval_ref = Column(String(255), nullable=True)
    consent_type = Column(String(100), nullable=True)
    deidentification_method = Column(String(255), nullable=True)
    
    differential_privacy_applied = Column(Boolean, default=False, server_default=text("false"), nullable=True)
    dp_epsilon = Column(Numeric(precision=10, scale=4), nullable=True)
    
    sensitivity_class = Column(Enum("standard", "high_stigma", "critical", name="sensitivity_class"), default="standard", server_default=text("'standard'"), nullable=False)
    persistent_identifier = Column(String(500), nullable=True)
    license_type = Column(String(100), nullable=True)
    synthetic_data_pct = Column(Numeric(precision=5, scale=2), nullable=True)
    access_control_method = Column(String(255), nullable=True)
    linked_model_ids = Column(JSONB, nullable=True)
    
    data_dictionary_uploaded = Column(Boolean, default=False, server_default=text("false"), nullable=True)
    provenance_pipeline_available = Column(Boolean, default=False, server_default=text("false"), nullable=True)
    github_repo_url = Column(String(500), nullable=True)
    changelog_provided = Column(Boolean, default=False, server_default=text("false"), nullable=True)
    version_format = Column(String(50), nullable=True)
    
    raw_form_json = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    assessment = relationship("Assessment", back_populates="metadata_form")
