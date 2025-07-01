# backend/services/pricing_logic.py

from typing import Dict, Any
from bson import ObjectId
from models.quote_model import Quote
from schemas.quote_schema import QuoteCreateSchema

# Función original (sigue disponible si hay lugares que la llamen directamente desde payload):
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
        "suggestions": []
    }


# Nueva función que lee datos directamente de MongoDB antes de calcular:
async def calculate_quote_summary_from_db(quote_id: str) -> dict:
    """
    1) Convierte quote_id a ObjectId y trae el documento de la cotización.
    2) Calcula el resumen usando únicamente los datos ya almacenados en la BD.
    """
    try:
        oid = ObjectId(quote_id)
    except Exception:
        raise ValueError("ID de cotización inválido")

    quote_obj = await Quote.get(oid)
    if not quote_obj:
        raise ValueError("Cotización no encontrada")

    # Leer subdocumentos desde quote_obj
    printer = quote_obj.printer
    filament = quote_obj.filament
    energy = quote_obj.energy
    model = quote_obj.model
    commercial = quote_obj.commercial

    # Cálculo de gramos usados y desperdiciados
    grams_used = model.model_weight + (model.supports and model.support_weight or 0)
    grams_wasted = model.supports and model.support_weight or 0
    waste_percentage = (grams_wasted / grams_used * 100) if grams_used else 0

    # Costo de material (filamento)
    material_cost = (filament.price_per_kg / 1000) * grams_used

    # Costo de energía
    energy_cost = (printer.watts / 1000) * model.print_time * energy.kwh_cost

    # Costo de máquina
    machine_cost = printer.hourly_cost * model.print_time

    # Costos comerciales y margen/impuestos
    labor_cost = commercial.labor
    post_cost = commercial.post_processing
    subtotal = material_cost + energy_cost + machine_cost + labor_cost + post_cost
    margin_amount = subtotal * commercial.margin
    tax_amount = (subtotal + margin_amount) * commercial.taxes
    estimated_total_cost = subtotal + margin_amount + tax_amount

    return {
        "grams_used": round(grams_used, 2),
        "grams_wasted": round(grams_wasted, 2),
        "waste_percentage": round(waste_percentage, 2),
        "estimated_total_cost": round(estimated_total_cost, 2),
        "suggestions": []
    }


# Generación de recomendaciones inteligentes (usa directamente el objeto Quote cargado desde DB)
def generate_optimization(quote: Quote) -> Dict[str, Any]:
    """
    Genera tres modos de optimización (fast, economic, balanced) a partir de una cotización existente.
    Recibe un objeto Quote (ya cargado desde la BD).
    """
    # --- Valores originales ---
    speed_old    = quote.printer.speed
    layer_old    = quote.model.layer_height
    infill_old   = quote.model.infill
    support_old  = quote.model.support_weight or 0.0
    model_weight = quote.model.model_weight
    time_old     = quote.model.print_time

    # Precios y costos
    price_per_g   = quote.filament.price_per_kg / 1000.0
    cost_kwh      = quote.energy.kwh_cost
    watts         = quote.printer.watts
    cost_per_hour = quote.printer.hourly_cost

    # Función auxiliar para calcular resultados a partir de nuevos parámetros
    def _calc_results(speed_new, layer_new, infill_new, support_new) -> Dict[str, Any]:
        if infill_old > 0:
            model_weight_new = model_weight * (infill_new / infill_old)
        else:
            model_weight_new = model_weight

        fact_layer  = layer_old / layer_new if layer_new > 0 else 1.0
        fact_speed  = speed_old / speed_new if speed_new > 0 else 1.0
        fact_infill = (infill_new / infill_old) if infill_old > 0 else 1.0
        time_new = time_old * fact_layer * fact_speed * fact_infill

        grams_used_new   = model_weight_new + support_new
        grams_wasted_new = support_new
        waste_pct_new = (grams_wasted_new / grams_used_new * 100.0) if grams_used_new > 0 else 0.0

        material_cost = grams_used_new * price_per_g
        energy_cost   = (watts / 1000.0) * time_new * cost_kwh
        machine_cost  = time_new * cost_per_hour
        total_cost    = material_cost + energy_cost + machine_cost

        return {
            "print_time": round(time_new, 2),
            "grams_used": round(grams_used_new, 2),
            "grams_wasted": round(grams_wasted_new, 2),
            "waste_percentage": round(waste_pct_new, 2),
            "material_cost": round(material_cost, 2),
            "energy_cost": round(energy_cost, 2),
            "machine_cost": round(machine_cost, 2),
            "total_cost": round(total_cost, 2),
        }

    # --- Modo ⚡ “Rápido” ---
    speed_fast = min(speed_old * 1.10, 300.0)
    layer_fast = min(layer_old * 1.10, 1.0)
    infill_fast  = infill_old
    support_fast = support_old * 0.90
    results_fast = _calc_results(speed_fast, layer_fast, infill_fast, support_fast)

    # --- Modo 💲 “Económico” ---
    infill_candidate = infill_old * 0.80
    infill_econ = infill_candidate if infill_candidate >= 5.0 else 5.0
    support_econ = support_old * 0.85
    results_econ = _calc_results(speed_old, layer_old, infill_econ, support_econ)

    # --- Modo ⚖️ “Balanceado” ---
    speed_bal = min(speed_old * 1.05, 300.0)
    layer_bal = min(layer_old * 1.05, 1.0)
    infill_candidate_bal = infill_old * 0.90
    infill_bal = infill_candidate_bal if infill_candidate_bal >= 5.0 else 5.0
    support_bal = support_old * 0.90
    results_bal = _calc_results(speed_bal, layer_bal, infill_bal, support_bal)

    return {
        "fast": {
            "new_parameters": {
                "speed": round(speed_fast, 2),
                "layer_height": round(layer_fast, 3),
                "infill": round(infill_fast, 2),
                "support_weight": round(support_fast, 2),
            },
            "results": results_fast,
        },
        "economic": {
            "new_parameters": {
                "speed": round(speed_old, 2),
                "layer_height": round(layer_old, 3),
                "infill": round(infill_econ, 2),
                "support_weight": round(support_econ, 2),
            },
            "results": results_econ,
        },
        "balanced": {
            "new_parameters": {
                "speed": round(speed_bal, 2),
                "layer_height": round(layer_bal, 3),
                "infill": round(infill_bal, 2),
                "support_weight": round(support_bal, 2),
            },
            "results": results_bal,
        },
    }
