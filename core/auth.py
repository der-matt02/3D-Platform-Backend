# 3D-Quotes-Backned/core/auth.py

import os
from pathlib import Path

from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import ValidationError

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from models.user_model import User
from schemas.user_schema import TokenDataSchema
from core.config import settings

# -------------------- Hashing de contraseñas --------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """
    Recibe la contraseña en texto plano y devuelve el hash (bcrypt).
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica que 'plain_password' coincida con el 'hashed_password'.
    """
    return pwd_context.verify(plain_password, hashed_password)


# -------------------- Configuración de JWT --------------------
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hora

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crea un JWT con el diccionario 'data' (incluir 'sub': username),
    y le añade fecha de expiración (claim 'exp').
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Dependencia que extrae al usuario actual del JWT.
    - Decodifica el token.
    - Obtiene 'sub' como username.
    - Busca el objeto User.username == sub.
    - Si no existe o no está activo, lanza 401.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenDataSchema(username=username)
    except (JWTError, ValidationError):
        raise credentials_exception

    user = await User.find_one(User.username == token_data.username)
    if user is None or not user.is_active:
        raise credentials_exception
    return user
