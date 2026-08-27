from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Accesorio(Base):
    __tablename__ = "accesorio"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150), unique=True)
    costo: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    precio_venta: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    stock_actual: Mapped[int] = mapped_column(Integer, default=0)

    movimientos: Mapped[list["MovimientoInventario"]] = relationship(
        back_populates="accesorio", cascade="all, delete-orphan"
    )


class MovimientoInventario(Base):
    __tablename__ = "movimiento_inventario"

    id: Mapped[int] = mapped_column(primary_key=True)
    accesorio_id: Mapped[int] = mapped_column(ForeignKey("accesorio.id"), index=True)
    tipo: Mapped[str] = mapped_column(String(20))
    cantidad: Mapped[int] = mapped_column(Integer)
    motivo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    accesorio: Mapped["Accesorio"] = relationship(back_populates="movimientos")
