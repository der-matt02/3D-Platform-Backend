# backend/services/quote_service.py

from typing import List, Optional
from bson import ObjectId
from datetime import datetime, UTC

from schemas.quote_schema import QuoteCreateSchema, QuoteUpdateSchema, QuoteOutSchema
from models.quote_model import Quote, Printer, Filament, Energy, ModelData, Commercial, Summary
from repositories import quote_repository

from services.pricing_logic import calculate_quote_summary, calculate_quote_summary_from_db, generate_optimization


# Crear cotización con cálculo de resumen basado en datos de BD
async def create_quote(user_id: str, data: QuoteCreateSchema) -> QuoteOutSchema:
    """
    1) Construye el objeto Quote desde payload (incluyendo un summary provisional).
    2) Inserta en MongoDB.
    3) Vuelve a cargar desde BD con get(id).
    4) Calcula resumen con calculate_quote_summary_from_db(id).
    5) Asigna summary real y guarda de nuevo.
    6) Retorna DTO de salida.
    """
    # 1) Calcular un summary provisional a partir del payload, para pasar validación
    provisional_summary = calculate_quote_summary(data)
    summary_obj = Summary(**provisional_summary)

    # 2) Crear instancia de Quote incluyendo ese summary provisional
    quote = Quote(
        user_id=ObjectId(user_id),
        quote_name=data.quote_name,
        printer=Printer(**data.printer.model_dump()),
        filament=Filament(**data.filament.model_dump()),
        energy=Energy(**data.energy.model_dump()),
        model=ModelData(**data.model.model_dump()),
        commercial=Commercial(**data.commercial.model_dump()),
        summary=summary_obj,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )

    # 3) Insertar en MongoDB
    await quote.insert()

    # 4) Recargar desde BD
    saved = await Quote.get(quote.id)
    if not saved:
        # Si no se encuentra, devolver el objeto inicial (con summary provisional)
        return QuoteOutSchema(
            id=str(quote.id),
            user_id=str(quote.user_id),
            quote_name=quote.quote_name,
            printer=quote.printer.model_dump(),
            filament=quote.filament.model_dump(),
            energy=quote.energy.model_dump(),
            model=quote.model.model_dump(),
            commercial=quote.commercial.model_dump(),
            summary=quote.summary.model_dump(),
            created_at=quote.created_at,
            updated_at=quote.updated_at
        )

    # 5) Calcular summary real usando datos desde BD
    summary_data = await calculate_quote_summary_from_db(str(saved.id))
    saved.summary = Summary(**summary_data)

    # 6) Guardar nuevamente con summary real
    saved.updated_at = datetime.now(UTC)
    await saved.save()

    # 7) Retornar DTO de salida
    return QuoteOutSchema(
        id=str(saved.id),
        user_id=str(saved.user_id),
        quote_name=saved.quote_name,
        printer=saved.printer.model_dump(),
        filament=saved.filament.model_dump(),
        energy=saved.energy.model_dump(),
        model=saved.model.model_dump(),
        commercial=saved.commercial.model_dump(),
        summary=saved.summary.model_dump(),
        created_at=saved.created_at,
        updated_at=saved.updated_at
    )


# Obtener cotización por ID
async def get_quote_by_id(quote_id: str) -> Optional[QuoteOutSchema]:
    quote = await quote_repository.get_quote_by_id(quote_id)
    if not quote:
        return None
    return QuoteOutSchema(
        id=str(quote.id),
        user_id=str(quote.user_id),
        quote_name=quote.quote_name,
        printer=quote.printer.model_dump(),
        filament=quote.filament.model_dump(),
        energy=quote.energy.model_dump(),
        model=quote.model.model_dump(),
        commercial=quote.commercial.model_dump(),
        summary=quote.summary.model_dump(),
        created_at=quote.created_at,
        updated_at=quote.updated_at
    )


# Obtener todas las cotizaciones del usuario actual
async def get_user_quotes(user_id: str) -> List[QuoteOutSchema]:
    quotes = await quote_repository.get_quotes_by_user(ObjectId(user_id))
    return [
        QuoteOutSchema(
            id=str(q.id),
            user_id=str(q.user_id),
            quote_name=q.quote_name,
            printer=q.printer.model_dump(),
            filament=q.filament.model_dump(),
            energy=q.energy.model_dump(),
            model=q.model.model_dump(),
            commercial=q.commercial.model_dump(),
            summary=q.summary.model_dump(),
            created_at=q.created_at,
            updated_at=q.updated_at
        )
        for q in quotes
    ]


# Editar una cotización y recalcular summary basado en datos de BD
async def update_quote(quote_id: str, data: QuoteUpdateSchema) -> Optional[QuoteOutSchema]:
    """
    1) Convierte quote_id a ObjectId y trae el documento de BD.
    2) Asigna los campos modificados desde payload.
    3) Guarda cambios parciales.
    4) Recarga desde BD con get(id).
    5) Calcula summary desde BD.
    6) Asigna summary y guarda de nuevo.
    7) Retorna DTO de salida.
    """
    try:
        oid = ObjectId(quote_id)
    except Exception:
        return None

    # 1) Cargar documento existente
    quote_obj = await Quote.get(oid)
    if not quote_obj:
        return None

    # 2) Asignar subdocumentos visibles
    payload = data.model_dump()
    quote_obj.quote_name = payload["quote_name"]
    quote_obj.printer    = Printer(**payload["printer"])
    quote_obj.filament   = Filament(**payload["filament"])
    quote_obj.energy     = Energy(**payload["energy"])
    quote_obj.model      = ModelData(**payload["model"])
    quote_obj.commercial = Commercial(**payload["commercial"])

    # 3) Guardar cambios sin summary
    quote_obj.updated_at = datetime.now(UTC)
    await quote_obj.save()

    # 4) Recargar desde BD
    saved = await Quote.get(oid)
    if not saved:
        return None

    # 5) Recalcular summary basado en datos persistidos
    summary_data = await calculate_quote_summary_from_db(quote_id)
    saved.summary = Summary(**summary_data)

    # 6) Guardar de nuevo con summary actualizado
    saved.updated_at = datetime.now(UTC)
    await saved.save()

    # 7) Retornar DTO de salida
    return QuoteOutSchema(
        id=str(saved.id),
        user_id=str(saved.user_id),
        quote_name=saved.quote_name,
        printer=saved.printer.model_dump(),
        filament=saved.filament.model_dump(),
        energy=saved.energy.model_dump(),
        model=saved.model.model_dump(),
        commercial=saved.commercial.model_dump(),
        summary=saved.summary.model_dump(),
        created_at=saved.created_at,
        updated_at=saved.updated_at
    )


# Eliminar una cotización
async def delete_quote(quote_id: str) -> bool:
    return await quote_repository.delete_quote(quote_id)
