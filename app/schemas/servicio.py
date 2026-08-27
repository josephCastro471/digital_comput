from decimal import Decimal

from pydantic import BaseModel, ConfigDict, model_validator

from app.models.servicio import TipoPrecio


class EscalonPrecioIn(BaseModel):
    cantidad_desde: int
    cantidad_hasta: int | None = None
    precio_unitario: Decimal


class EscalonPrecioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cantidad_desde: int
    cantidad_hasta: int | None
    precio_unitario: Decimal


class ServicioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    categoria: str
    tipo_precio: TipoPrecio
    precio_base: Decimal | None
    activo: bool
    escalones: list[EscalonPrecioOut] = []


def validar_escalones(escalones: list[EscalonPrecioIn]) -> None:
    ordenados = sorted(escalones, key=lambda e: e.cantidad_desde)
    for i, escalon in enumerate(ordenados):
        if escalon.precio_unitario <= 0:
            raise ValueError("precio_unitario debe ser mayor a 0")
        if escalon.cantidad_desde < 1:
            raise ValueError("cantidad_desde debe ser mayor o igual a 1")
        if escalon.cantidad_hasta is not None and escalon.cantidad_hasta < escalon.cantidad_desde:
            raise ValueError("cantidad_hasta no puede ser menor que cantidad_desde")
        if i > 0:
            anterior = ordenados[i - 1]
            if anterior.cantidad_hasta is None:
                raise ValueError("solo el ultimo escalon puede quedar abierto (sin cantidad_hasta)")
            if escalon.cantidad_desde <= anterior.cantidad_hasta:
                raise ValueError("los escalones no pueden solaparse")


class ServicioCreate(BaseModel):
    nombre: str
    categoria: str
    tipo_precio: TipoPrecio
    precio_base: Decimal | None = None
    escalones: list[EscalonPrecioIn] = []

    @model_validator(mode="after")
    def validar_precio(self) -> "ServicioCreate":
        if self.tipo_precio == TipoPrecio.FIJO:
            if self.precio_base is None or self.precio_base <= 0:
                raise ValueError("precio_base es obligatorio y mayor a 0 para tipo_precio=fijo")
            if self.escalones:
                raise ValueError("un servicio de tipo fijo no lleva escalones")
        elif self.tipo_precio == TipoPrecio.ESCALONADO:
            if self.precio_base is not None:
                raise ValueError("un servicio escalonado no usa precio_base, el precio sale de los escalones")
            if not self.escalones:
                raise ValueError("tipo_precio=escalonado requiere al menos un escalon")
            validar_escalones(self.escalones)
        elif self.tipo_precio == TipoPrecio.VARIABLE:
            if self.escalones:
                raise ValueError("un servicio de tipo variable no lleva escalones")
        return self


class ServicioUpdate(BaseModel):
    nombre: str | None = None
    categoria: str | None = None
    precio_base: Decimal | None = None
    activo: bool | None = None
    escalones: list[EscalonPrecioIn] | None = None
