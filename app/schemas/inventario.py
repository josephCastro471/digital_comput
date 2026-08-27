from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AccesorioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    costo: Decimal
    precio_venta: Decimal
    stock_actual: int


class AccesorioCreate(BaseModel):
    nombre: str
    costo: Decimal = Field(ge=0)
    precio_venta: Decimal = Field(ge=0)
    stock_actual: int = Field(default=0, ge=0)


class AccesorioUpdate(BaseModel):
    nombre: str | None = None
    costo: Decimal | None = Field(default=None, ge=0)
    precio_venta: Decimal | None = Field(default=None, ge=0)


class MovimientoInventarioCreate(BaseModel):
    tipo: Literal["entrada", "salida"]
    cantidad: int = Field(gt=0)
    motivo: str | None = None


class MovimientoInventarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    accesorio_id: int
    tipo: str
    cantidad: int
    motivo: str | None
    fecha: datetime
