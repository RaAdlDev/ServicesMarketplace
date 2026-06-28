from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from core.settings import settings
from datetime import datetime, timedelta, timezone

oauth = OAuth2PasswordBearer(tokenUrl="auth/login")

password_context = CryptContext(schemes=["bcrypt"] )


def hash_password(plain_password: str):
    return password_context.hash(plain_password)

def verify_password(plain_password: str, data_password: str):
    return password_context.verify(plain_password, data_password)

def return_token(token_data: dict):
    to_encode = token_data.copy()
    expire_time = datetime.now(timezone.utc) + timedelta(minutes= settings.token_duration)
    to_encode.update({"exp": expire_time})
    return jwt.encode(to_encode, settings.secret_key, settings.algorithm)