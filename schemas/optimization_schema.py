# backend/schemas/optimization_schema.py

from pydantic import BaseModel
from typing import Dict

class ModeParameters(BaseModel):
    speed: float
    layer_height: float
    infill: float
    support_weight: float

class ModeResults(BaseModel):
    print_time: float
    grams_used: float
    grams_wasted: float
    waste_percentage: float
    material_cost: float
    energy_cost: float
    machine_cost: float
    total_cost: float

class OptimizationMode(BaseModel):
    new_parameters: ModeParameters
    results: ModeResults

class OptimizationOutputSchema(BaseModel):
    fast: OptimizationMode
    economic: OptimizationMode
    balanced: OptimizationMode
