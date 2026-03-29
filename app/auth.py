from typing import Optional
import secrets, os
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials, HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from .database import get_db, get_user_by_id, verify_user_password, update_user_profile, change_user_password, get_user_by_username
from .models import UserRegister, UserLogin, UserUpdate
import sqlite3

ADMIN_USER = os.getenv("ADMIN_USER")
ADMIN_PASS = os.getenv("ADMIN_PASS")
JWT_SECRET = os.getenv("JWT_SECRET", "your-super-secret-key-change-this")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 365

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
security = HTTPBasic()
bearer_scheme = HTTPBearer(auto_error=False)

def authenticate_admin(credentials: HTTPBasicCredentials = Depends(security)):
    is_user = secrets.compare_digest(credentials.username, ADMIN_USER)
    is_pass = secrets.compare_digest(credentials.password, ADMIN_PASS)
    if not (is_user and is_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect login or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

def get_user_by_username(username: str):
    with get_db() as conn:
        try:
            cur = conn.execute('SELECT id, email, username, hashed_password, approved, email_verified, avatar_url FROM users WHERE username = ?', (username,))
            row = cur.fetchone()
            if row:
                return {
                    "id": row[0], "email": row[1], "username": row[2],
                    "hashed_password": row[3], "approved": bool(row[4]),
                    "email_verified": bool(row[5]) if len(row) > 5 else True,
                    "avatar_url": row[6] if len(row) > 6 else None
                }
        except:
            cur = conn.execute('SELECT id, email, username, hashed_password, approved FROM users WHERE username = ?', (username,))
            row = cur.fetchone()
            if row:
                return {
                    "id": row[0], "email": row[1], "username": row[2],
                    "hashed_password": row[3], "approved": bool(row[4]),
                    "email_verified": True, "avatar_url": None
                }
    return None

def create_user(email: str, username: str, password: str):
    hashed = pwd_context.hash(password)
    with get_db() as conn:
        try:
            try:
                conn.execute('INSERT INTO users (email, username, hashed_password, email_verified) VALUES (?, ?, ?, 0)',
                             (email, username, hashed))
            except:
                conn.execute('INSERT INTO users (email, username, hashed_password) VALUES (?, ?, ?)',
                             (email, username, hashed))
            conn.commit()
            cursor = conn.execute('SELECT id FROM users WHERE username = ?', (username,))
            return cursor.fetchone()[0]
        except sqlite3.IntegrityError:
            return None

def verify_password(plain: str, hashed: str):
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if not user["approved"]:
        raise HTTPException(status_code=403, detail="Account not approved")
    if not user.get("email_verified", True):
        raise HTTPException(status_code=403, detail="Email not verified")
    return user

async def get_current_user_from_query(token: Optional[str] = None):
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if not user["approved"]:
        raise HTTPException(status_code=403, detail="Account not approved")
    if not user.get("email_verified", True):
        raise HTTPException(status_code=403, detail="Email not verified")
    return user