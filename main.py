from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.database import initiate_database       # Función que inicializa Beanie
from api.auth import router as auth_router         # Router de /auth
from api.quotes import router as quotes_router     # Router de CRUD de cotizaciones
from api.quote_optimization import router as optimization_router  # Router de optimización

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

# Registrar ruta de optimización de cotizaciones
app.include_router(optimization_router)

# Nueva implementacion
from api.inverse_quote import router as inverse_quote_router

app.include_router(inverse_quote_router)
