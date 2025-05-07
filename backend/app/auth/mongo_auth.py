"""
MongoDB authentication module for the Product Review Analyzer.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
import os
from dotenv import load_dotenv

from ..mongodb import get_collection
from ..models.mongo_models import MongoUser

# Load environment variables
load_dotenv()

# Get secret key from environment
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")

# Token model
class Token(BaseModel):
    access_token: str
    token_type: str

# Token data model
class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[str] = None

def verify_password(plain_password, hashed_password):
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Hash password."""
    return pwd_context.hash(password)

def get_user(username: str):
    """Get user from MongoDB by username."""
    users_collection = get_collection("users")
    user = users_collection.find_one({"username": username})
    if user:
        return user
    return None

def authenticate_user(username: str, password: str):
    """Authenticate user."""
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(tz=timezone.utc) + expires_delta
    else:
        expire = datetime.now(tz=timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current user from token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: str = payload.get("id")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username, user_id=user_id)
    except JWTError:
        raise credentials_exception
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user = Depends(get_current_user)):
    """Get current active user."""
    if not current_user.get("is_active", True):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_user_optional(token: str = Depends(oauth2_scheme)):
    """Get current user from token, but don't raise an exception if token is invalid."""
    try:
        return await get_current_user(token)
    except HTTPException:
        return None

async def get_current_user_ws(websocket):
    """Get current user from WebSocket connection."""
    try:
        # Get token from query parameters
        token = websocket.query_params.get("token")
        if not token:
            # Try getting token from headers
            auth_header = websocket.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
            else:
                raise HTTPException(status_code=401, detail="Missing authentication token")

        # Decode token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: str = payload.get("id")

        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication token")

        # Get user from database
        user = get_user(username=username)
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")

        # Check if user is active
        if not user.get("is_active", True):
            raise HTTPException(status_code=400, detail="Inactive user")

        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication error: {str(e)}")

def create_user(username: str, email: str, password: str, is_admin: bool = False):
    """Create a new user in MongoDB."""
    users_collection = get_collection("users")

    # Check if user already exists
    if users_collection.find_one({"username": username}):
        return None
    if users_collection.find_one({"email": email}):
        return None

    # Create new user
    hashed_password = get_password_hash(password)
    user = {
        "username": username,
        "email": email,
        "hashed_password": hashed_password,
        "is_active": True,
        "is_admin": is_admin,
        "created_at": datetime.now()
    }

    # Insert user into MongoDB
    result = users_collection.insert_one(user)
    user["_id"] = result.inserted_id

    return user
