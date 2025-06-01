from beanie import Document
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional
from datetime import datetime, UTC
from bson import ObjectId


from models.enums.filament_enums import FilamentType, FilamentColor, FilamentDiameter
from models.enums.printer_enums import PrinterType, NozzleSize, SupportType

# Subdocumento embebido con especificaciones de la impresora
class Printer(BaseModel):
    name: str = Field(..., min_length=2, max_length=30, description="Nombre de la impresora")
    watts: float = Field(..., gt=0, description="Consumo eléctrico en watts")
    type: PrinterType = Field(..., description="Tipo de impresora 3D")
    speed: float = Field(..., gt=0, le=300, description="Velocidad en mm/s (máx 300)")
    nozzle : NozzleSize = Field(..., description= "Diametro de boquilla")
    layer: float = Field(..., gt=0, le=1.0, description="Resolución de capa en mm")
    bed_temperature: float = Field(..., ge=0, le=120, description="Temperatura cama caliente (°C)")
    hotend_temperature: float = Field(..., ge=150, le=350, description="Temperatura del hotend (°C)")
    hourly_cost: float = Field(..., ge=1, le=500, description="Costo por hora de uso de impresora")

    @field_validator("name")
    def name_must_be_alphanumeric_or_spaces(v):
        if not v.replace(" ", "").isalnum():
            raise ValueError("El nombre debe contener solo letras, números y espacios")
        return v


# Subdocumento con los datos del filamento usado
class Filament(BaseModel):
    name: str = Field(..., min_length=2, max_length=40, description="Nombre del filamento")
    type: FilamentType = Field(..., description="Tipo de filamento")
    color: FilamentColor = Field(..., description="Color del filamento")
    diameter: FilamentDiameter = Field(..., description="Diametro del filamento")
    price_per_kg: float = Field(..., gt=1, le=100, description="Precio por kilogramo en rango realista")
    total_weight: float = Field(..., gt=0, description="Peso total usado en gramos")

    @field_validator("name")
    def name_must_be_text(v):
        if not v.replace(" ", "").isalpha():
            raise ValueError("El nombre debe contener solo letras y espacios")
        return v


# Subdocumento con costo energético
class Energy(BaseModel):
    kwh_cost: float = Field(..., gt=0, description="Costo por kilovatio/hora")


# Subdocumento con los datos técnicos del modelo a imprimir
class ModelData(BaseModel):
    model_weight: float = Field(..., gt=0, description="Peso del modelo (g)")
    print_time: float = Field(..., gt=0, description="Tiempo estimado de impresión (horas)")
    infill: float = Field(..., gt=0, le=100, description="Porcentaje de relleno")
    supports: Optional[bool] = Field(default=False, description="¿Usa soportes?")
    support_type: Optional[SupportType] = Field(None, description="Tipo de soporte")
    support_weight: Optional[float] = Field(0, description="Peso de los soportes (g)")
    layer_height: float = Field(..., gt=0, le=1.0, description="Altura de capa en mm")

    @model_validator(mode="after")
    def check_support_dependencies(self) -> "ModelData":
        if self.supports:
            if not self.support_type:
                raise ValueError("Debe especificar el tipo de soporte si supports=True")
            if not self.support_weight or self.support_weight <= 0:
                raise ValueError("Debe especificar un peso de soporte válido si supports=True")
        else:
            if self.support_type or (self.support_weight and self.support_weight > 0):
                raise ValueError("No debe incluir tipo ni peso de soporte si supports=False")
        return self


# Subdocumento con los costos comerciales
class Commercial(BaseModel):
    labor: Optional[float] = Field(default=0, ge=0, le=500, description="Mano de obra (opcional)")
    post_processing: Optional[float] = Field(default=0, ge=0, le=500, description="Costo de postprocesado (opcional)")
    margin: float = Field(..., ge=0, le=1.0, description="Margen de ganancia (entre 0 y 1)")
    taxes: Optional[float] = Field(default=0, ge=0, le=1.0, description="Porcentaje de impuestos (opcional)")

    @field_validator("margin")
    def validate_margin_format(cls, v):
        if v < 0 or v > 1:
            raise ValueError("El margen debe ser un valor decimal entre 0 y 1 (ej. 0.3 = 30%)")
        return v


# Subdocumento resumen del cálculo
class Summary(BaseModel):
    estimated_total_cost: float = Field(..., ge=0, description="Costo total estimado")
    grams_used: float = Field(..., ge=0, description="Gramos utilizados")
    grams_wasted: float = Field(..., ge=0, description="Gramos desperdiciados")
    waste_percentage: float = Field(..., ge=0, le=100, description="Porcentaje de desecho")
    suggestions: Optional[list[str]] = Field(default_factory=list, description="Sugerencias automáticas")


# Documento principal que se guarda en MongoDB
class Quote(Document):
    user_id: ObjectId = Field(..., description="ID del usuario que creó la cotización")
    quote_name: str = Field(..., min_length=3, max_length=60, description="Nombre de la cotización")
    printer: Printer
    filament: Filament
    energy: Energy
    model: ModelData
    commercial: Commercial
    summary: Summary
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "quotes"  # Nombre de la colección en MongoDB

    class Config:
        arbitrary_types_allowed = True  # Para permitir el uso de ObjectId

    '''
    arbitrary_types_allowed = True 
    Esto indica a Pydantic que acepte tipos como ObjectId, 
    que no son parte del estándar de Pydantic, 
    pero que usamos en MongoDB para los IDs.
    '''
