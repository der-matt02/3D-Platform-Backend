# backend/routers/quote_router.py

from fastapi import APIRouter, Depends, HTTPException, status, Path
from typing import List, Any
from bson import ObjectId

from schemas.quote_schema import QuoteCreateSchema, QuoteUpdateSchema, QuoteOutSchema
from services.quote_service import create_quote, get_quote_by_id, get_user_quotes, update_quote, delete_quote
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
        return await create_quote(str(current_user.id), data)
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
        return await get_user_quotes(str(current_user.id))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener cotizaciones: {str(e)}")


@router.get("/{quote_id}", response_model=QuoteOutSchema)
async def get_quote_endpoint(
    quote_id: str = Path(..., description="ID de la cotización a obtener"),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Obtiene una cotización específica por su ID (si pertenece al usuario).
    """
    try:
        ObjectId(quote_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID inválido")

    quote = await get_quote_by_id(quote_id)
    if not quote or quote.user_id != str(current_user.id):
        raise HTTPException(status_code=404, detail="Cotización no encontrada")

    return quote


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
        ObjectId(quote_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID inválido")

    try:
        updated = await update_quote(quote_id, data)
        if not updated or updated.user_id != str(current_user.id):
            raise HTTPException(status_code=404, detail="Cotización no encontrada o sin permisos")
        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar la cotización: {str(e)}")


@router.delete("/{quote_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quote_endpoint(
    quote_id: str,
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Elimina la cotización si pertenece al usuario autenticado.
    """
    try:
        success = await delete_quote(quote_id)
        if not success:
            raise HTTPException(status_code=404, detail="Cotización no encontrada")
        return
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar la cotización: {str(e)}")
