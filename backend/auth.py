"""
Elysium Health — Landing / marketing auth.
JWT-based sign-in and registration; in-memory user store with optional file persistence.
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr

# ─── Config ──────────────────────────────────────────────────
AUTH_SECRET = os.getenv("AUTH_SECRET", "change-me-in-production-elysium")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days
USERS_FILE = Path(__file__).resolve().parent / "auth_users.json"

# Use pbkdf2_sha256 to avoid platform-specific bcrypt issues and 72-byte limits.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
security = HTTPBearer(auto_error=False)


# ─── Models ───────────────────────────────────────────────────
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    email: str
    name: Optional[str] = None


def _hash_password(password: str) -> str:
    return pwd_context.hash(password)


def _verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _create_token(sub: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": sub, "exp": expire}
    return jwt.encode(payload, AUTH_SECRET, algorithm=ALGORITHM)


def _decode_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, AUTH_SECRET, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


# ─── User store (in-memory + optional file) ────────────────────
def _load_users() -> dict:
    """Load users from file if present."""
    data: dict = {}
    if USERS_FILE.exists():
        try:
            data = json.loads(USERS_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return data


def _save_users(users: dict) -> None:
    """Persist users to file."""
    try:
        USERS_FILE.write_text(json.dumps(users, indent=2))
    except OSError:
        pass


_users: dict = {}


def _get_users() -> dict:
    global _users
    if not _users:
        _users = _load_users()
    return _users


def _persist_users() -> None:
    _save_users(_get_users())


def register_user(email: str, password: str, name: Optional[str] = None) -> dict:
    """Create user. Raises ValueError if email exists."""
    users = _get_users()
    key = email.lower().strip()
    if key in users:
        raise ValueError("An account with this email already exists.")
    users[key] = {
        "email": key,
        "password_hash": _hash_password(password),
        "name": (name or "").strip() or None,
    }
    _persist_users()
    return {"email": users[key]["email"], "name": users[key]["name"]}


def authenticate_user(email: str, password: str) -> Optional[dict]:
    """Return user dict if credentials valid."""
    users = _get_users()
    key = email.lower().strip()
    if key not in users:
        return None
    u = users[key]
    if not _verify_password(password, u["password_hash"]):
        return None
    return {"email": u["email"], "name": u.get("name")}


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[UserOut]:
    """Dependency: return current user from Bearer token or None."""
    if not credentials or credentials.scheme != "Bearer":
        return None
    sub = _decode_token(credentials.credentials)
    if not sub:
        return None
    users = _get_users()
    if sub not in users:
        return None
    u = users[sub]
    return UserOut(email=u["email"], name=u.get("name"))


def get_current_user(
    user: Optional[UserOut] = Depends(get_current_user_optional),
) -> UserOut:
    """Dependency: require authenticated user or 401."""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def create_access_token(email: str) -> str:
    """Return a JWT for the given user email (e.g. after login/register)."""
    return _create_token(email.lower().strip())
