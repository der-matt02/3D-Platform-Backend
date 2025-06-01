from typing import List, Optional
from models.quote_model import Quote
from schemas.quote_schema import QuoteCreateSchema, QuoteUpdateSchema
from bson import ObjectId


# Crear nueva cotización
async def create_quote(user_id: ObjectId, data: QuoteCreateSchema) -> Quote:
    quote = Quote(
        user_id=user_id,
        quote_name=data.quote_name,
        printer=data.printer,
        filament=data.filament,
        energy=data.energy,
        model=data.model,
        commercial=data.commercial,
        summary=await calculate_summary(data)  # Placeholder
    )
    return await quote.insert()


# Obtener cotización por ID NOTA: para mostrar o validar propiedad
async def get_quote_by_id(quote_id: str) -> Optional[Quote]:
    return await Quote.get(ObjectId(quote_id))


# Obtener todas las cotizaciones de un usuario
async def get_quotes_by_user(user_id: ObjectId) -> List[Quote]:
    return await Quote.find(Quote.user_id == user_id).to_list()


# Actualizar una cotización
async def update_quote(quote_id: str, data: QuoteUpdateSchema) -> Optional[Quote]:
    oid = ObjectId(quote_id)
    # find_one_and_update retorna el documento antiguo o el nuevo, según configuración
    updated = await Quote.find_one_and_update(
        {"_id": oid},
        {"$set": data.dict()},
        return_document=True  # si usas Motor directamente. En Beanie usa `set_only=True, fetch_new=True` o el método correspondiente
    )
    return updated


# Eliminar cotización
async def delete_quote(quote_id: str) -> bool:
    quote = await Quote.get(ObjectId(quote_id))
    if not quote:
        return False
    await quote.delete()
    return True


def calculate_waste_percentage(used: float, total: float) -> float:
    if total == 0:
        return 0.0
    waste = total - used
    return (waste / total) * 100


async def calculate_summary(data):
    # datos base para calculo
    model_weight = data.model.peso_modelo
    support_weight = data.model.peso_soportes
    filament_weight = data.filament.peso_total

    # filamento usado
    grams_used = model_weight + support_weight
    grams_wasted = filament_weight - grams_used
    waste_percentage = calculate_waste_percentage(grams_used, filament_weight)

    # costo
    hours = data.model.tiempo_impresion
    energy_cost = hours * (data.printer.watts / 1000) * data.energy.costo_kwh
    printing_cost = hours * data.commercial.costo_hora

    subtotal = energy_cost + printing_cost + data.commercial.mano_obra + data.commercial.postprocesado
    subtotal_with_margin = subtotal * (1 + data.commercial.margen)
    total_cost = subtotal_with_margin * (1 + data.commercial.impuestos)

    # Sugerencias
    suggestions = []
    if data.model.infill > 50:
        suggestions.append("Reduce infill: it's above 50%")
    if data.model.soportes and data.model.tipo_soporte == "árbol":
        suggestions.append("Consider avoiding tree supports if possible")
    if data.model.altura_capa > 0.3:
        suggestions.append("Reduce layer height to improve print quality")
    if waste_percentage > 20:
        suggestions.append("Optimize supports or adjust model weight")

    return {
        "grams_used": grams_used,
        "grams_wasted": grams_wasted,
        "waste_percentage": waste_percentage,
        "estimated_total_cost": round(total_cost, 2),
        "suggestions": suggestions
    }

