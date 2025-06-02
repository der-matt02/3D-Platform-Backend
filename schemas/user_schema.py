from pydantic import BaseModel, EmailStr, Field, validator


class UserCreateSchema(BaseModel):
    """
    Esquema para registro de usuario:
      - username (único, 3–30 chars)
      - email (único)
      - password
      - confirm_password
    """
    username: str = Field(
        ...,
        min_length=3,
        max_length=30,
        example="juanperez",
        description="Nombre de usuario único (3–30 caracteres)"
    )
    email: EmailStr = Field(..., example="juan@ejemplo.com")
    password: str = Field(..., min_length=6, example="MiClave123")
    confirm_password: str = Field(..., min_length=6, example="MiClave123")

    @validator("confirm_password")
    def passwords_match(cls, v, values):
        pw = values.get("password")
        if pw is None or v != pw:
            raise ValueError("Las contraseñas no coinciden")
        return v


class UserLoginSchema(BaseModel):
    """
    Esquema para login de usuario:
      - identifier: puede ser username o email
      - password
    """
    identifier: str = Field(
        ...,
        example="juanperez",
        description="Nombre de usuario o correo electrónico"
    )
    password: str = Field(..., example="MiClave123")


class TokenSchema(BaseModel):
    """
    Respuesta de registro/login:
      - access_token (JWT)
      - token_type = "bearer"
    """
    access_token: str
    token_type: str = "bearer"


class TokenDataSchema(BaseModel):
    """
    Datos extraídos de un JWT válido:
      - username (el 'sub' dentro del token)
    """
    username: str
