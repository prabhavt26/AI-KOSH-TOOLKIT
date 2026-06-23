from sqlalchemy import Column, String, Boolean, TIMESTAMP, func, text
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.database import Base

class ApiKey(Base):
    __tablename__ = "api_keys"

    key_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("uuid_generate_v4()"))
    key_hash = Column(String(64), nullable=False, unique=True, index=True)
    key_prefix = Column(String(10), nullable=False)
    owner_name = Column(String(255), nullable=False)
    role = Column(String(20), default="submitter", server_default=text("'submitter'"), nullable=False)
    is_active = Column(Boolean, default=True, server_default=text("true"), nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    last_used_at = Column(TIMESTAMP(timezone=True), nullable=True)
    expires_at = Column(TIMESTAMP(timezone=True), nullable=True)
