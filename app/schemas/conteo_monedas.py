from datetime import datetime
from decimal import Decimal, InvalidOperation

from pydantic import BaseModel, ConfigDict, field_validator


class ConteoMonedasCreate(BaseModel):
    denominaciones: dict[str, int]
    nota: str | None = None

    @field_validator("denominaciones")
    @classmethod
    def validar_denominaciones(cls, v: dict[str, int]) -> dict[str, int]:
        if not v:
            raise ValueError("denominaciones no puede estar vacio")
        for clave, cantidad in v.items():
            try:
                valor = Decimal(clave)
            except InvalidOperation as exc:
                raise ValueError(f"'{clave}' no es una denominacion valida") from exc
            if valor <= 0:
                raise ValueError(f"la denominacion '{clave}' debe ser mayor a 0")
            if cantidad < 0:
                raise ValueError(f"la cantidad para '{clave}' no puede ser negativa")
        return v


class ConteoMonedasOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fecha: datetime
    denominaciones: dict[str, int]
    total: Decimal
    nota: str | None
