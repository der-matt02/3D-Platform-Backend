from bson import ObjectId
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from models.enums.filament_enums import FilamentType, FilamentColor, FilamentDiameter
from models.enums.printer_enums import PrinterType, NozzleSize, SupportType

# Esquema para impresora
class PrinterSchema(BaseModel):
    name: str # nombre de la impresora
    watts: float # potencia en watts
    type: PrinterType # tipo de impresora
    speed: float # velocidad de impresión
    nozzle: NozzleSize # diámetro de la boquilla (nozzle)
    layer: float # altura de capa
    bed_temperature: float # temperatura de cama
    hotend_temperature: float# temperatura hotend (calentador de filamento)
    hourly_cost: float

# Esquema para filamento
class FilamentSchema(BaseModel):
    name: str # nombre del filamento
    type: FilamentType # tipo de filamento
    diameter: FilamentDiameter # diámetro del filamento
    price_per_kg: float # precio por kilogramo
    color: FilamentColor # color del filamento
    total_weight: float # peso total disponible

# Esquema para energía
class EnergySchema(BaseModel):
    kwh_cost: float # costo por kilovatio-hora

# Esquema para datos del modelo
class ModelDataSchema(BaseModel):
    model_weight: float # peso del modelo
    print_time: float # tiempo estimado de impresión
    infill: float # porcentaje de relleno (infill)
    supports: Optional[bool] = False  # si tiene soportes o no
    support_type: Optional[SupportType] = None  # tipo de soporte (opcional)
    support_weight: float = 0 # peso de los soportes
    layer_height: float # altura de cada capa

# Esquema para datos comerciales
class CommercialSchema(BaseModel):
    labor: Optional[float] = 0 # costo de mano de obra
    post_processing: Optional[float] = 0 # costo del postprocesado
    margin: float # margen de ganancia
    taxes: Optional[float] = 0 # impuestos aplicados

# Esquema para resumen de cotización
class SummarySchema(BaseModel):
    estimated_total_cost: float # costo total estimado
    grams_used: float # gramos usados en la impresión
    grams_wasted: float # gramos desechados
    waste_percentage: float # porcentaje de desperdicio
    suggestions: Optional[List[str]] = []  # sugerencias opcionales

# Esquema para crear cotizaciones
class QuoteCreateSchema(BaseModel):
    quote_name: str # nombre de la cotización
    printer: PrinterSchema # datos de la impresora
    filament: FilamentSchema # datos del filamento
    energy: EnergySchema # datos de energía
    model: ModelDataSchema # datos del modelo
    commercial: CommercialSchema # datos comerciales

    class Config:
        from_attributes = True

# Esquema para actualizar cotizaciones (todos los campos son opcionales)
class QuoteUpdateSchema(BaseModel):
    quote_name: Optional[str] # nombre de la cotización (opcional)
    printer: Optional[PrinterSchema] # datos de impresora (opcional)
    filament: Optional[FilamentSchema] # datos del filamento (opcional)
    energy: Optional[EnergySchema] # datos de energía (opcional)
    model: Optional[ModelDataSchema] # datos del modelo (opcional)
    commercial: Optional[CommercialSchema] # datos comerciales (opcional)

    class Config:
        from_attributes = True

# Esquema para mostrar cotizaciones
class QuoteOutSchema(BaseModel):
    id: str = Field(alias= "_id") # id de la cotización
    user_id: str # id del usuario que creó la cotización
    quote_name: str # nombre de la cotización
    printer: PrinterSchema # datos de la impresora
    filament: FilamentSchema # datos del filamento
    energy: EnergySchema # datos de energía
    model: ModelDataSchema # datos del modelo
    commercial: CommercialSchema # datos comerciales
    summary: SummarySchema # resumen de la cotización
    created_at: datetime # fecha de creación
    updated_at: datetime # fecha de actualización

    class Config:
        from_attributes = True
        populate_by_name = True
        json_encoders = {ObjectId: str}
