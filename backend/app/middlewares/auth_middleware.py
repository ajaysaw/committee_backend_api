from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.utils.security import decode_token
from app.models.models import User, UserSession
from app.models.enums import UserRole
from datetime import datetime, timezone

security_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    # Verify session is active
    session = (
        db.query(UserSession)
        .filter(
            UserSession.token == token,
            UserSession.is_active == True,
            UserSession.expires_at > datetime.now(timezone.utc),
            UserSession.deleted_at == None,
        )
        .first()
    )
    if session is None:
        raise HTTPException(status_code=401, detail="Session expired or invalidated")

    user = db.query(User).filter(User.id == int(user_id), User.deleted_at == None).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


async def require_member(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in (UserRole.ADMIN, UserRole.MEMBER):
        raise HTTPException(status_code=403, detail="Access denied")
    return current_user
