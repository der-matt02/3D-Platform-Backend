from typing import Dict
from schemas.quote_schema import QuoteCreateSchema


# Diagnóstico de cotización
def calculate_quote_summary(data: QuoteCreateSchema) -> dict:
    # Material
    price_per_gram = data.filament.price_per_kg / 1000
    total_weight = data.model.model_weight + data.model.support_weight
    material_cost = total_weight * price_per_gram

    # Energía
    kwh_used = (data.printer.watts / 1000) * data.model.print_time
    energy_cost = kwh_used * data.energy.kwh_cost

    # Impresión
    machine_cost = data.model.print_time * data.printer.hourly_cost
    printing_cost = material_cost + energy_cost + machine_cost

    # Comercial
    extra_cost = data.commercial.labor + data.commercial.post_processing
    base_cost = printing_cost + extra_cost
    with_margin = base_cost * (1 + data.commercial.margin)
    final_price = with_margin * (1 + data.commercial.taxes)

    # Diagnóstico
    grams_used = total_weight
    grams_wasted = data.model.support_weight
    waste_percentage = (grams_wasted / grams_used) * 100 if grams_used > 0 else 0

    return {
        "estimated_total_cost": round(final_price, 2),
        "grams_used": round(grams_used, 2),
        "grams_wasted": round(grams_wasted, 2),
        "waste_percentage": round(waste_percentage, 2),
        "suggestions": []  # Placeholder si se quiere extender
    }


# 💡 Generación de recomendaciones inteligentes
def generate_optimization(summary: dict, data: QuoteCreateSchema) -> Dict:
    suggestions = {}
    messages = []

    if data.model.infill > 20:
        suggestions["infill"] = 15
        messages.append("Reduce el infill a 15% para minimizar material.")

    if data.model.layer_height < 0.2:
        suggestions["layer_height"] = 0.3
        messages.append("Aumenta la altura de capa a 0.3mm para reducir el tiempo de impresión.")

    if data.printer.nozzle in ["0.2", "0.4"] and data.model.print_time > 5:
        suggestions["nozzle"] = "0.6"
        messages.append("Considera boquillas 0.6mm para impresiones más rápidas.")

    if summary["waste_percentage"] > 15 and data.model.supports:
        suggestions["support_type"] = "Árbol"
        messages.append("Reduce el tipo de soporte a 'Árbol' si es posible, para minimizar el desperdicio.")

    if data.filament.price_per_kg > 22:
        suggestions["price_per_kg"] = 18.0
        messages.append("Usa un material más económico (< $20/kg) si es posible.")

    return {
        "optimized_suggestion": suggestions,
        "recommendation_summary": messages
    }
