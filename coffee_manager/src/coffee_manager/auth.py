import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, APIKeyHeader
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from coffee_manager.config import settings
from coffee_manager.database import get_db
from coffee_manager.models import ApiKey, User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer()
api_key_header = APIKeyHeader(name="X-Api-Key", auto_error=False)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": user_id, "role": role, "exp": expire},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    db: Session = Depends(get_db),
) -> User:
    payload = decode_token(credentials.credentials)
    user = db.get(User, payload["sub"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    return user


def generate_api_key() -> tuple[str, str, str]:
    raw = "cof_" + secrets.token_urlsafe(32)
    prefix = raw[:16]
    key_hash = pwd_context.hash(raw)
    return raw, prefix, key_hash


def get_distributor_by_api_key(
    x_api_key: Annotated[str | None, Depends(api_key_header)],
    db: Session = Depends(get_db),
) -> ApiKey:
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="API key required"
        )
    prefix = x_api_key[:16]
    candidates = (
        db.query(ApiKey)
        .filter(ApiKey.key_prefix == prefix, ApiKey.active.is_(True))
        .all()
    )
    for key in candidates:
        if verify_password(x_api_key, key.key_hash):
            return key
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key"
    )
