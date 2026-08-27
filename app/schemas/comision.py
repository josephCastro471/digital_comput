from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProveedorComisionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    comision_pct: Decimal
    aplica_iva: bool
    iva_pct: Decimal


class ProveedorComisionUpdate(BaseModel):
    comision_pct: Decimal | None = Field(default=None, ge=0, le=100)
    aplica_iva: bool | None = None
    iva_pct: Decimal | None = Field(default=None, ge=0, le=100)


class ComisionCalcularIn(BaseModel):
    proveedor_id: int
    valor_recibir: Decimal = Field(gt=0)


class ComisionCalculadaOut(BaseModel):
    proveedor_id: int
    valor_recibir: Decimal
    comision: Decimal
    iva_sobre_comision: Decimal
    valor_cobrado: Decimal


class TransaccionComisionCreate(BaseModel):
    proveedor_id: int
    valor_recibir: Decimal = Field(gt=0)


class TransaccionComisionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    proveedor_id: int
    valor_recibir: Decimal
    comision: Decimal
    iva_sobre_comision: Decimal
    valor_cobrado: Decimal
    fecha: datetime
