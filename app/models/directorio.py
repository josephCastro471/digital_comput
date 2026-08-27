import enum

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TipoDirectorio(str, enum.Enum):
    EMPRESA = "empresa"
    CLIENTE = "cliente"


class Directorio(Base):
    __tablename__ = "directorio"

    id: Mapped[int] = mapped_column(primary_key=True)
    tipo: Mapped[TipoDirectorio] = mapped_column(Enum(TipoDirectorio, name="tipo_directorio", native_enum=False))
    nombre: Mapped[str] = mapped_column(String(150))
    codigo: Mapped[str | None] = mapped_column(String(100), nullable=True)
    red: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cedula_cuenta: Mapped[str | None] = mapped_column(String(50), nullable=True)
    nota: Mapped[str | None] = mapped_column(String(255), nullable=True)
