from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.schemas.arqueo import ArqueoCajaOut
from app.schemas.cuenta import CuentaOut


class VentasResumen(BaseModel):
    cantidad: int
    total: Decimal


class ComisionesResumen(BaseModel):
    cantidad: int
    total_comision: Decimal
    total_iva_sobre_comision: Decimal
    total_valor_cobrado: Decimal


class DashboardResumenOut(BaseModel):
    fecha: date
    ventas: VentasResumen
    comisiones: ComisionesResumen
    arqueos: list[ArqueoCajaOut]
    cuentas: list[CuentaOut]


class DashboardRangoOut(BaseModel):
    desde: date
    hasta: date
    ventas: VentasResumen
    comisiones: ComisionesResumen
    arqueos: list[ArqueoCajaOut]
    cuentas: list[CuentaOut]
