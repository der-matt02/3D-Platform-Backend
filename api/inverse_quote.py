from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Any
from models.inverse_model import InverseQuote

router = APIRouter(prefix="/inverse", tags=["Cotización Inversa"])

class InverseQuoteInput(BaseModel):
    presupuesto: float = Field(..., gt=0)
    peso_total: float = Field(..., gt=0)
    gramos_filamento: float = Field(..., gt=0)

class InverseQuoteOutput(BaseModel):
    tiempo: float
    infill: float
    altura: float

@router.post("/", response_model=InverseQuoteOutput)
async def calcular_cotizacion_inversa(data: InverseQuoteInput) -> Any:

    if data.peso_total == 0 or data.gramos_filamento == 0:
        return InverseQuoteOutput(tiempo=0, infill=0, altura=0)

    uso_material = data.peso_total / data.gramos_filamento
    presupuesto_alto = data.presupuesto > 20
    presupuesto_bajo = data.presupuesto < 15

    if presupuesto_bajo:
        infill_sugerido = 10.0
        tiempo_estimado = uso_material * 8
        altura_sugerida = 0.4
    elif presupuesto_alto:
        infill_sugerido = 80.0
        tiempo_estimado = uso_material * 12
        altura_sugerida = 0.2
    else:
        infill_sugerido = 40.0
        tiempo_estimado = uso_material * 10
        altura_sugerida = 0.3


    tiempo_final = round(tiempo_estimado, 2)
    infill_final = round(infill_sugerido, 1)
    altura_final = round(altura_sugerida, 2)


    inversa = InverseQuote(
        presupuesto=data.presupuesto,
        peso_total=data.peso_total,
        gramos_filamento=data.gramos_filamento,
        tiempo=tiempo_final,
        infill=infill_final,
        altura=altura_final
    )
    await inversa.insert()


    return InverseQuoteOutput(
        tiempo=inversa.tiempo,
        infill=inversa.infill,
        altura=inversa.altura
    )
