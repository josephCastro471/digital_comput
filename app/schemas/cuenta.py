from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.cuenta import TipoCuenta, TipoMovimiento


class CuentaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    tipo: TipoCuenta
    saldo_actual: Decimal
    saldo_inicial_dia: Decimal
    cupo_transaccional: Decimal | None
    cupo_utilizado: Decimal
    cupo_disponible: Decimal | None
    activa: bool
    creado_en: datetime


class MovimientoCuentaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cuenta_id: int
    tipo: TipoMovimiento
    monto: Decimal
    referencia_tipo: str | None
    referencia_id: int | None
    nota: str | None
    fecha: datetime


class MovimientoCuentaCreate(BaseModel):
    tipo: TipoMovimiento
    monto: Decimal
    referencia_tipo: str | None = None
    referencia_id: int | None = None
    nota: str | None = None

    @model_validator(mode="after")
    def validar_monto(self) -> "MovimientoCuentaCreate":
        if self.monto == 0:
            raise ValueError("monto no puede ser 0")
        if self.tipo != TipoMovimiento.AJUSTE and self.monto < 0:
            raise ValueError("monto debe ser positivo salvo en movimientos de ajuste")
        return self


class CuentaCupoUpdate(BaseModel):
    cupo_transaccional: Decimal = Field(ge=0)


class CuentaSaldoDiaIn(BaseModel):
    saldo: Decimal = Field(ge=0)


class CuentaCierreDiaIn(BaseModel):
    saldo_banco: Decimal = Field(ge=0)
    monto_retirado: Decimal = Field(ge=0, default=Decimal("0"))


class CuentaCierreDiaOut(BaseModel):
    recaudado: Decimal
    monto_retirado: Decimal
    saldo_inicial_dia: Decimal
    saldo_banco: Decimal
    nueva_base: Decimal
    cuenta: CuentaOut
