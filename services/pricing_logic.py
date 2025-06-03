# backend/services/pricing_logic.py

from typing import Dict, Any
from schemas.quote_schema import QuoteCreateSchema
from models.quote_model import Quote


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
    #with_margin = base_cost * (1 + (data.commercial.margin / 100))
    final_price = with_margin * (1 + data.commercial.taxes)
    #final_price = with_margin * (1 + (data.commercial.taxes / 100))

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
def generate_optimization(quote: Quote) -> Dict[str, Any]:
    """
    Genera tres modos de optimización (fast, economic, balanced) a partir de una cotización existente.
    Retorna un diccionario con, para cada modo:
      - new_parameters: { speed, layer_height, infill, support_weight }
      - results: { print_time, grams_used, grams_wasted, waste_percentage,
                   material_cost, energy_cost, machine_cost, total_cost }
    """

    # --- Valores originales ---
    speed_old    = quote.printer.speed                    # mm/s
    layer_old    = quote.model.layer_height               # mm
    infill_old   = quote.model.infill                     # %
    support_old  = quote.model.support_weight or 0.0      # g
    model_weight = quote.model.model_weight               # g
    time_old     = quote.model.print_time                 # h

    # Precios y costos
    price_per_g   = quote.filament.price_per_kg / 1000.0   # USD por gramo
    cost_kwh      = quote.energy.kwh_cost                  # USD por kWh
    watts         = quote.printer.watts                    # W
    cost_per_hour = quote.printer.hourly_cost              # USD por hora

    # Función auxiliar para calcular resultados a partir de nuevos parámetros
    def _calc_results(speed_new, layer_new, infill_new, support_new) -> Dict[str, Any]:
        # 1) Peso de modelo nuevo (solo cambia si infill varía)
        if infill_old > 0:
            model_weight_new = model_weight * (infill_new / infill_old)
        else:
            model_weight_new = model_weight

        # 2) Nuevo tiempo de impresión
        #    - fact_layer  = layer_old / layer_new
        #    - fact_speed  = speed_old / speed_new
        #    - fact_infill = infill_new / infill_old (si infill_old > 0)
        fact_layer  = layer_old / layer_new if layer_new > 0 else 1.0
        fact_speed  = speed_old / speed_new if speed_new > 0 else 1.0
        fact_infill = (infill_new / infill_old) if infill_old > 0 else 1.0
        time_new = time_old * fact_layer * fact_speed * fact_infill

        # 3) Gramos usados y desperdicio
        grams_used_new   = model_weight_new + support_new
        grams_wasted_new = support_new
        waste_pct_new = (grams_wasted_new / grams_used_new * 100.0) if grams_used_new > 0 else 0.0

        # 4) Costos
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
    speed_fast = speed_old * 1.10
    if speed_fast > 300.0:
        speed_fast = 300.0

    layer_fast = layer_old * 1.10
    if layer_fast > 1.0:
        layer_fast = 1.0

    infill_fast  = infill_old               # sin cambio en infill
    support_fast = support_old * 0.90        # –10 % en soportes

    results_fast = _calc_results(
        speed_new=speed_fast,
        layer_new=layer_fast,
        infill_new=infill_fast,
        support_new=support_fast,
    )

    # --- Modo 💲 “Económico” ---
    speed_econ = speed_old                  # sin cambio en velocidad
    layer_econ = layer_old                  # sin cambio en capa

    infill_candidate = infill_old * 0.80
    infill_econ = infill_candidate if infill_candidate >= 5.0 else 5.0

    support_econ = support_old * 0.85       # –15 % en soportes

    results_econ = _calc_results(
        speed_new=speed_econ,
        layer_new=layer_econ,
        infill_new=infill_econ,
        support_new=support_econ,
    )

    # --- Modo ⚖️ “Balanceado” ---
    speed_bal = speed_old * 1.05
    if speed_bal > 300.0:
        speed_bal = 300.0

    layer_bal = layer_old * 1.05
    if layer_bal > 1.0:
        layer_bal = 1.0

    infill_candidate_bal = infill_old * 0.90
    infill_bal = infill_candidate_bal if infill_candidate_bal >= 5.0 else 5.0

    support_bal = support_old * 0.90        # –10 % en soportes

    results_bal = _calc_results(
        speed_new=speed_bal,
        layer_new=layer_bal,
        infill_new=infill_bal,
        support_new=support_bal,
    )

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
                "speed": round(speed_econ, 2),
                "layer_height": round(layer_econ, 3),
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
