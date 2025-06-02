# 3D-Quotes-Backned/main.py

import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.database import initiate_database       # <— Usa la función que inicializa Beanie
from api.auth import router as auth_router         # <— Tu router de /auth
from api.quotes import router as quotes_router     # <— Tu router de cotizaciones existente

app = FastAPI(title="3D Quotes API")

# ───────────────────────────────────────────────────────────────────────
# Configurar CORS para permitir peticiones desde el frontend
origins = [
    "http://localhost:3000",
    "http://localhost:5173",  # Puerto por defecto de Vite
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],    # GET, POST, PUT, DELETE, OPTIONS, etc.
    allow_headers=["*"],    # Authorization, Content-Type, etc.
)
# ───────────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def on_startup():
    # Inicializa la base de datos (incluye Quote y User)
    await initiate_database()

# Registrar rutas de autenticación
app.include_router(auth_router, prefix="/auth")

# Registrar rutas de cotizaciones
app.include_router(quotes_router)
