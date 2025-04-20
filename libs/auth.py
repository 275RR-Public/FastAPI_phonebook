from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta, timezone
import jwt
from libs.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from libs.models import User
from fastapi import HTTPException, Depends, Request
from typing import List, Annotated

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# REST API uses OAuth2.0 JWT with Roles
# Hardcoded users bypasses paying for Cloud Services
users = {
    "readuser": {
        "username": "readuser",
        "hashed_password": pwd_context.hash("readpassword"),
        "role": "Read"
    },
    "rwuser": {
        "username": "rwuser",
        "hashed_password": pwd_context.hash("rwpassword"),
        "role": "ReadWrite"
    }
}

# Function to create JWT token
def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Dependency to get current user from token
def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role")
        if username is None or role is None:
            raise credentials_exception
        return User(username=username, role=role)
    except jwt.PyJWTError:
        raise credentials_exception

# Dependency to enforce role-based access
def require_roles(roles: List[str]):
    def dependency(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient privileges")
        return current_user
    return dependency


def get_username_from_token(request: Request) -> str:
    """
    Extracts and decodes the JWT token from the request headers to retrieve the username.
    Returns "unknown" if the token is missing, invalid, or cannot be decoded.
    """
    try:
        token = request.headers.get("Authorization", "").split("Bearer ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            return "unknown"
        return username
    except (IndexError, AttributeError, jwt.PyJWTError):
        # Handle cases where the token is missing, malformed, or invalid
        return "unknown"