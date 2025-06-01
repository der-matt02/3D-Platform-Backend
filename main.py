from fastapi import FastAPI
from core.database import initiate_database
from api.quotes import router as quotes_router

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    await initiate_database()

    # ----------------------------
    # 1) Habilitar CORS
    # ----------------------------
    # Ajusta el origin (o lista de origins) según tu entorno


origins = [
    "http://localhost:5173",  # puerto por defecto de Vite
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # O usa ["*"] para permitir todo en dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(quotes_router)
