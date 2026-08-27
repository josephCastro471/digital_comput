import enum
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class EstadoArqueo(str, enum.Enum):
    ABIERTO = "abierto"
    CERRADO = "cerrado"


class ArqueoCaja(Base):
    __tablename__ = "arqueo_caja"

    id: Mapped[int] = mapped_column(primary_key=True)
    fecha_apertura: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    fecha_cierre: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    saldo_apertura: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("40.00"))
    saldo_cierre: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    ganancia_neta: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    estado: Mapped[EstadoArqueo] = mapped_column(
        Enum(EstadoArqueo, name="estado_arqueo", native_enum=False), default=EstadoArqueo.ABIERTO
    )

    detalles: Mapped[list["ArqueoDetalle"]] = relationship(
        back_populates="arqueo", cascade="all, delete-orphan"
    )


class ArqueoDetalle(Base):
    __tablename__ = "arqueo_detalle"

    id: Mapped[int] = mapped_column(primary_key=True)
    arqueo_id: Mapped[int] = mapped_column(ForeignKey("arqueo_caja.id"), index=True)
    denominacion: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    cantidad: Mapped[int] = mapped_column(Integer)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2))

    arqueo: Mapped["ArqueoCaja"] = relationship(back_populates="detalles")
