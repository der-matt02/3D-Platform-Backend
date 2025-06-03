# backend/api/quote_optimization.py

from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId

from models.quote_model import Quote
from services.pricing_logic import generate_optimization
from schemas.optimization_schema import OptimizationOutputSchema
from core.auth import get_current_user # o donde tengas tu dependencia de usuario

router = APIRouter(prefix="/api/quotes", tags=["quotes"])

@router.get("/{quote_id}/optimize", response_model=OptimizationOutputSchema)
async def optimize_quote_endpoint(
    quote_id: str,
    current_user = Depends(get_current_user)
):
    # 1) Recuperar la cotización de MongoDB
    try:
        quote_obj = await Quote.get(ObjectId(quote_id))
    except:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")

    if not quote_obj:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")

    # 2) Verificar que el usuario sea propietario
    if quote_obj.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso para ver esta cotización")

    # 3) Generar las tres propuestas de optimización
    optimization = generate_optimization(quote_obj)

    return optimization
