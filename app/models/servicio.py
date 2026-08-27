import enum
from decimal import Decimal

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TipoPrecio(str, enum.Enum):
    FIJO = "fijo"
    ESCALONADO = "escalonado"
    VARIABLE = "variable"


class Servicio(Base):
    __tablename__ = "servicio"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150))
    categoria: Mapped[str] = mapped_column(String(100))
    tipo_precio: Mapped[TipoPrecio] = mapped_column(Enum(TipoPrecio, name="tipo_precio", native_enum=False))
    precio_base: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)

    escalones: Mapped[list["EscalonPrecio"]] = relationship(
        back_populates="servicio",
        cascade="all, delete-orphan",
        order_by="EscalonPrecio.cantidad_desde",
    )


class EscalonPrecio(Base):
    __tablename__ = "escalon_precio"

    id: Mapped[int] = mapped_column(primary_key=True)
    servicio_id: Mapped[int] = mapped_column(ForeignKey("servicio.id"), index=True)
    cantidad_desde: Mapped[int] = mapped_column(Integer)
    cantidad_hasta: Mapped[int | None] = mapped_column(Integer, nullable=True)
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(12, 2))

    servicio: Mapped["Servicio"] = relationship(back_populates="escalones")
