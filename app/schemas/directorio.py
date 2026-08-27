from pydantic import BaseModel, ConfigDict

from app.models.directorio import TipoDirectorio


class DirectorioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tipo: TipoDirectorio
    nombre: str
    codigo: str | None
    red: str | None
    cedula_cuenta: str | None
    nota: str | None


class DirectorioCreate(BaseModel):
    tipo: TipoDirectorio
    nombre: str
    codigo: str | None = None
    red: str | None = None
    cedula_cuenta: str | None = None
    nota: str | None = None


class DirectorioUpdate(BaseModel):
    tipo: TipoDirectorio | None = None
    nombre: str | None = None
    codigo: str | None = None
    red: str | None = None
    cedula_cuenta: str | None = None
    nota: str | None = None
