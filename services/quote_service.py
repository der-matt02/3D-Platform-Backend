from typing import List, Optional
from schemas.quote_schema import QuoteCreateSchema, QuoteUpdateSchema
from models.quote_model import Quote, Printer, Filament, Energy, ModelData, Commercial, Summary
from repositories import quote_repository
from bson import ObjectId
from datetime import datetime, UTC

from services.pricing_logic import calculate_quote_summary, generate_optimization

from schemas.quote_schema import QuoteOutSchema
# Crear cotización con cálculo de resumen
async def create_quote(user_id: str, data: QuoteCreateSchema) -> Quote:
    # Cálculo de resumen (puede ir mejorando luego)
    # Cálculo real del resumen técnico
    summary_data = calculate_quote_summary(data)
    # Generación de recomendaciones inteligentes (si decides guardarlas)
    optimization = generate_optimization(summary_data, data)
    summary_data["suggestions"] = optimization["recommendation_summary"]

    # Convertir dict a objeto Summary
    summary_obj = Summary(**summary_data)
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
    await quote.insert() # problema interno de ide que no detecta metodos asincronos beanie
    #return quote
    #return QuoteOutSchema.model_validate(quote)
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

# Obtener cotización por ID (usada en GET o validación de propietario)
async def get_quote_by_id(quote_id: str) -> Optional[Quote]:
    return await quote_repository.get_quote_by_id(quote_id)


# Obtener todas las cotizaciones del usuario actual
async def get_user_quotes(user_id: ObjectId) -> List[Quote]:
    quotes = await quote_repository.get_quotes_by_user(user_id)
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


# Editar una cotización
async def update_quote(quote_id: str, data: QuoteUpdateSchema) -> Optional[Quote]:
    """
    1) Convierte quote_id a ObjectId
    2) Obtiene la cotización (Quote) con Beanie
    3) Asigna cada sección del payload a la instancia
    3.1) Recalcula el summary
    4) Actualiza updated_at y salva con .save()
    5) Retorna la instancia actualizada (o None si no existe)
    """
    try:
        oid = ObjectId(quote_id)
    except Exception:
        return None

    # 1) Traer la cotización (instancia de Quote) por su _id
    quote_obj = await Quote.get(oid)
    if not quote_obj:
        return None

    # 2) Convertir el payload a dict
    payload = data.model_dump()

    # 3) Asignar valores uno a uno
    quote_obj.quote_name = payload["quote_name"]
    quote_obj.printer    = Printer(**payload["printer"])
    quote_obj.filament   = Filament(**payload["filament"])
    quote_obj.energy     = Energy(**payload["energy"])
    quote_obj.model      = ModelData(**payload["model"])
    quote_obj.commercial = Commercial(**payload["commercial"])

    # 3.1) Recalcular el summary usando calculate_quote_summary(data)
    summary_data = calculate_quote_summary(data)
    # Ya no intentamos generar “recommendation_summary” porque generate_optimization
    # no retorna esa clave en este proyecto.
    quote_obj.summary = Summary(**summary_data)

    # 4) Actualizar fecha de modificación
    quote_obj.updated_at = datetime.now(UTC)

    # 5) Guardar cambios
    await quote_obj.save()

    return quote_obj

# Eliminar una cotización
async def delete_quote(quote_id: str) -> bool:
    return await quote_repository.delete_quote(quote_id)