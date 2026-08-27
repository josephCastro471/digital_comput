from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class VentaItemCreate(BaseModel):
    servicio_id: int
    cantidad: int = Field(ge=1)
    precio_unitario: Decimal | None = None


class VentaCreate(BaseModel):
    cuenta_id: int | None = None
    items: list[VentaItemCreate]

    @field_validator("items")
    @classmethod
    def no_vacio(cls, v: list[VentaItemCreate]) -> list[VentaItemCreate]:
        if not v:
            raise ValueError("una venta requiere al menos un item")
        return v


class VentaItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    servicio_id: int
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal


class VentaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fecha: datetime
    total: Decimal
    cuenta_id: int | None
    items: list[VentaItemOut] = []
