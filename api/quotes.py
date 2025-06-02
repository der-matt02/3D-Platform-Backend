from fastapi import APIRouter, Depends, HTTPException, status, Path
from typing import List, Any
from bson import ObjectId

from schemas.quote_schema import QuoteCreateSchema, QuoteUpdateSchema, QuoteOutSchema
from services.quote_service import create_quote, get_user_quotes, update_quote, delete_quote
from core.auth import get_current_user
from models.user_model import User

router = APIRouter(prefix="/api/quotes", tags=["Quotes"])


@router.post("/", response_model=QuoteOutSchema, status_code=status.HTTP_201_CREATED)
async def create_quote_endpoint(
    data: QuoteCreateSchema,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Crea una cotización asociada al usuario autenticado.
    """
    try:
        quote = await create_quote(str(current_user.id), data)
        return QuoteOutSchema.model_validate(quote)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear la cotización: {str(e)}")


@router.get("/", response_model=List[QuoteOutSchema])
async def list_user_quotes(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Lista las cotizaciones que pertenecen al usuario autenticado.
    """
    try:
        return await get_user_quotes(ObjectId(str(current_user.id)))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener cotizaciones: {str(e)}")


@router.put("/{quote_id}", response_model=QuoteOutSchema)
async def update_quote_endpoint(
    data: QuoteUpdateSchema,
    quote_id: str = Path(..., description="ID de la cotización a actualizar"),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Actualiza la cotización con ID=quote_id, si pertenece al usuario autenticado.
    """
    try:
        _ = ObjectId(quote_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID inválido")

    try:
        updated_model = await update_quote(quote_id, data)
        if not updated_model:
            raise HTTPException(status_code=404, detail="Cotización no encontrada")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar la cotización: {str(e)}")

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
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Elimina la cotización si pertenece al usuario autenticado.
    """
    try:
        deleted = await delete_quote(quote_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Cotización no encontrada")
        return
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar la cotización: {str(e)}")
