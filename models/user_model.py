# 3D-Quotes-Backned/models/user_model.py

from datetime import datetime

from beanie import Document
from pydantic import Field, EmailStr


class User(Document):
    """
    Modelo de usuario en MongoDB (Beanie Document).
    Campos: username único, email único y contraseña hasheada.
    """
    username: str = Field(
        ...,
        min_length=3,
        max_length=30,
        unique=True,
        description="Nombre de usuario único (3–30 caracteres)"
    )
    email: EmailStr = Field(
        ...,
        unique=True,
        description="Correo electrónico único"
    )
    hashed_password: str = Field(
        ...,
        description="Contraseña hasheada (bcrypt)"
    )
    is_active: bool = Field(
        True,
        description="Si el usuario está activo"
    )
    is_superuser: bool = Field(
        False,
        description="Si es usuario administrador"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Fecha de creación"
    )

    class Settings:
        name = "users"  # Nombre de la colección en MongoDB

    class Config:
        json_schema_extra = {
            "example": {
                "username": "juanperez",
                "email": "juan@ejemplo.com",
                "hashed_password": "$2b$12$...",
                "is_active": True,
                "is_superuser": False,
                "created_at": "2025-01-01T12:00:00Z"
            }
        }
