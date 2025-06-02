from fastapi import APIRouter, HTTPException, status
from pymongo.errors import DuplicateKeyError

from models.user_model import User
from schemas.user_schema import UserCreateSchema, UserLoginSchema, TokenSchema
from core.auth import hash_password, verify_password, create_access_token

router = APIRouter(tags=["auth"])


@router.post("/register", response_model=TokenSchema, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreateSchema):
    """
    Registra un nuevo usuario:
    - username único
    - email único
    - password + confirm_password
    Devuelve un JWT si todo es correcto.
    """
    # 1) Verificar que el username no exista
    if await User.find_one(User.username == user_in.username):
        raise HTTPException(status_code=400, detail="El nombre de usuario ya está en uso")

    # 2) Verificar que el email no exista
    if await User.find_one(User.email == user_in.email):
        raise HTTPException(status_code=400, detail="El correo electrónico ya está registrado")

    # 3) Crear el usuario con contraseña hasheada
    user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
    )
    try:
        await user.insert()
    except DuplicateKeyError:
        # MongoDB arroja DuplicateKeyError si username o email ya están en la base
        raise HTTPException(status_code=400, detail="Usuario o correo ya existente")

    # 4) Generar token JWT con 'sub' = user.username
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/token", response_model=TokenSchema)
async def login(login_data: UserLoginSchema):
    """
    Login de usuario:
    - identifier: puede ser username o email
    - password
    Devuelve JWT si las credenciales son correctas.
    """
    # 1) Buscar usuario por username o por email (filtro Mongo $or)
    user = await User.find_one({
        "$or": [
            {"username": login_data.identifier},
            {"email": login_data.identifier}
        ]
    })
    if not user:
        raise HTTPException(status_code=400, detail="Usuario o contraseña incorrectos")

    # 2) Verificar contraseña
    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Usuario o contraseña incorrectos")

    # 3) Generar token con `sub = user.username`
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}
