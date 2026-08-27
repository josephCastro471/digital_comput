from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ProveedorComision(Base):
    __tablename__ = "proveedor_comision"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True)
    comision_pct: Mapped[Decimal] = mapped_column(Numeric(6, 4), default=Decimal("0.0000"))
    aplica_iva: Mapped[bool] = mapped_column(Boolean, default=False)
    iva_pct: Mapped[Decimal] = mapped_column(Numeric(6, 4), default=Decimal("0.0000"))


class TransaccionComision(Base):
    __tablename__ = "transaccion_comision"

    id: Mapped[int] = mapped_column(primary_key=True)
    proveedor_id: Mapped[int] = mapped_column(ForeignKey("proveedor_comision.id"), index=True)
    valor_recibir: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    comision: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    iva_sobre_comision: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    valor_cobrado: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    proveedor: Mapped["ProveedorComision"] = relationship()
