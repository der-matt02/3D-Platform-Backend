from fastapi import APIRouter, Depends, HTTPException, status, Path
from typing import List, Any
from bson import ObjectId

from schemas.quote_schema import QuoteCreateSchema, QuoteUpdateSchema, QuoteOutSchema
from services.quote_service import create_quote, get_user_quotes, update_quote, delete_quote

router = APIRouter(prefix="/api/quotes", tags=["Quotes"])


def get_current_user_id() -> str:
    return "664e0e871fe5e2bfe80c03de"


@router.post("/", response_model=QuoteOutSchema, status_code=status.HTTP_201_CREATED)
async def create_quote_endpoint(
    data: QuoteCreateSchema,
    user_id: str = Depends(get_current_user_id)
) -> Any:
    try:
        quote = await create_quote(user_id, data)
        return QuoteOutSchema.model_validate(quote)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear la cotización: {str(e)}")


@router.get("/", response_model=List[QuoteOutSchema])
async def list_user_quotes(
    user_id: str = Depends(get_current_user_id)
) -> Any:
    try:
        return await get_user_quotes(ObjectId(user_id))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener cotizaciones: {str(e)}")


@router.put("/{quote_id}", response_model=QuoteOutSchema)
async def update_quote_endpoint(
    data: QuoteUpdateSchema,  # ← viene en el body (JSON)
    quote_id: str = Path(..., description="ID de la cotización a actualizar"),
    user_id: str = Depends(get_current_user_id)
) -> Any:
    # 1) Validar que quote_id sea un ObjectId
    try:
        _ = ObjectId(quote_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID inválido")

    # 2) Llamar al servicio que actualiza y retorna la instancia
    try:
        updated_model = await update_quote(quote_id, data)
        if not updated_model:
            raise HTTPException(status_code=404, detail="Cotización no encontrada")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar la cotización: {str(e)}")

    # 3) Convertir a QuoteOutSchema y devolver
    try:
        return QuoteOutSchema(
            id=str(updated_model.id),
            user_id=str(updated_model.user_id),
            quote_name=updated_model.quote_name,
            printer=updated_model.printer.model_dump(),
            filament=updated_model.filament.model_dump(),
            energy=updated_model.energy.model_dump(),
            model=updated_model.model.model_dump(),
            commercial=updated_model.commercial.model_dump(),
            summary=updated_model.summary.model_dump(),
            created_at=updated_model.created_at,
            updated_at=updated_model.updated_at
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al serializar la cotización actualizada: {str(e)}"
        )


@router.delete("/{quote_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quote_endpoint(
    quote_id: str,
    user_id: str = Depends(get_current_user_id)
) -> None:
    try:
        deleted = await delete_quote(quote_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Cotización no encontrada")
        return
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar la cotización: {str(e)}")
