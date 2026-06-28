import hashlib
import jwt
from uuid import UUID
from typing import Optional
from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.config import settings
from app.models.user import User
from app.models.api_key import ApiKey
from app.models.assessment import Assessment

# Extractor for Authorization Header
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

async def get_current_user(
    request: Request,
    api_key_header_val: Optional[str] = Security(api_key_header),
    db: AsyncSession = Depends(get_async_db)
) -> User:
    """
    Dependency that authenticates the requester.
    Supports:
    1. Human Operators: HTTP-Only cookie 'session_token' (JWT).
    2. Programmatic API Keys: 'Authorization' header containing the Bearer token.
    """
    token: Optional[str] = None
    
    # 1. Try Cookie Authentication (Human Operators)
    cookie_token = request.cookies.get("session_token")
    if cookie_token:
        token = cookie_token
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid session token payload"
                )
            # Fetch user
            result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
            user = result.scalars().first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User session invalid or suspended"
                )
            return user
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session credentials"
            )

    # 2. Try API Key Authentication (Programmatic Developers)
    raw_key = api_key_header_val
    if raw_key:
        # Strip Bearer prefix if present
        if raw_key.startswith("Bearer "):
            token = raw_key[7:]
        else:
            token = raw_key
            
        # Compute SHA-256 hash of the incoming API Key
        key_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # Query ApiKey and load relationships
        stmt = select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.is_active == True)
        result = await db.execute(stmt)
        api_key_record = result.scalars().first()
        
        if not api_key_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or deactivated API Key"
            )
            
        # Fetch associated User
        user_result = await db.execute(select(User).where(User.id == api_key_record.user_id, User.is_active == True))
        user = user_result.scalars().first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API Key owner is suspended or deleted"
            )
        
        # Attach API key ID context dynamically to request state so assessment routes can track it
        request.state.api_key_id = api_key_record.key_id
        return user

    # Neither cookie nor header credentials provided
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated. Missing session cookie or API key header."
    )


async def get_current_active_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Verifies that the authenticated requester has the admin role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden. Admin privileges required."
        )
    return current_user


async def get_current_active_reviewer(
    current_user: User = Depends(get_current_user)
) -> User:
    """Verifies that the authenticated requester has the reviewer or admin role."""
    if current_user.role not in ["reviewer", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden. Reviewer privileges required."
        )
    return current_user


async def get_user_assessment(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
) -> Assessment:
    """
    Helper dependency to retrieve an assessment and enforce ownership boundaries (BOLA prevention).
    - Regular users can only access their own assessments.
    - Reviewers can access any assessment.
    - Admins are forbidden from viewing assessments (isolated boundary).
    """
    # Enforce admin boundary
    if current_user.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. System admins are strictly isolated from assessment data."
        )

    try:
        uuid_val = UUID(assessment_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment record not found"
        )

    stmt = select(Assessment).where(Assessment.assessment_id == uuid_val)
    result = await db.execute(stmt)
    assessment = result.scalars().first()
    
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment record not found"
        )
        
    # Enforce BOLA ownership checks
    if current_user.role != "reviewer" and assessment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You do not own this assessment."
        )
        
    return assessment
