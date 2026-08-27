from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.arqueo import EstadoArqueo


class ArqueoAbrirIn(BaseModel):
    saldo_apertura: Decimal = Decimal("40.00")


class ArqueoDetalleIn(BaseModel):
    denominacion: Decimal = Field(gt=0)
    cantidad: int = Field(ge=0)


class ArqueoCerrarIn(BaseModel):
    detalles: list[ArqueoDetalleIn]

    @field_validator("detalles")
    @classmethod
    def no_vacio(cls, v: list[ArqueoDetalleIn]) -> list[ArqueoDetalleIn]:
        if not v:
            raise ValueError("se requiere al menos un detalle de denominacion para cerrar el arqueo")
        return v


class ArqueoDetalleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    denominacion: Decimal
    cantidad: int
    subtotal: Decimal


class ArqueoCajaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fecha_apertura: datetime
    fecha_cierre: datetime | None
    saldo_apertura: Decimal
    saldo_cierre: Decimal | None
    ganancia_neta: Decimal | None
    estado: EstadoArqueo
    detalles: list[ArqueoDetalleOut] = []
