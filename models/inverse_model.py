from beanie import Document
from pydantic import Field
from datetime import datetime

class InverseQuote(Document):
    presupuesto: float = Field(..., gt=0)
    peso_total: float = Field(..., gt=0)
    gramos_filamento: float = Field(..., gt=0)

    tiempo: float
    infill: float
    altura: float

    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "inverse_quotes"  # nombre de la colección en MongoDB
