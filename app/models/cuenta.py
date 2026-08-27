import enum
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TipoCuenta(str, enum.Enum):
    EFECTIVO = "efectivo"
    CUPO_REVOLVENTE = "cupo_revolvente"
    FONDO_FIJO = "fondo_fijo"
    RED_RECAUDACION = "red_recaudacion"


class TipoMovimiento(str, enum.Enum):
    DEPOSITO = "deposito"
    RETIRO = "retiro"
    USO = "uso"
    AJUSTE = "ajuste"


class Cuenta(Base):
    __tablename__ = "cuenta"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True)
    tipo: Mapped[TipoCuenta] = mapped_column(Enum(TipoCuenta, name="tipo_cuenta", native_enum=False))
    saldo_actual: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    saldo_inicial_dia: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    cupo_transaccional: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    cupo_utilizado: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    activa: Mapped[bool] = mapped_column(Boolean, default=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    movimientos: Mapped[list["MovimientoCuenta"]] = relationship(
        back_populates="cuenta", order_by="MovimientoCuenta.fecha"
    )

    @property
    def cupo_disponible(self) -> Decimal | None:
        if self.cupo_transaccional is None:
            return None
        return self.cupo_transaccional - self.cupo_utilizado


class MovimientoCuenta(Base):
    __tablename__ = "movimiento_cuenta"

    id: Mapped[int] = mapped_column(primary_key=True)
    cuenta_id: Mapped[int] = mapped_column(ForeignKey("cuenta.id"), index=True)
    tipo: Mapped[TipoMovimiento] = mapped_column(Enum(TipoMovimiento, name="tipo_movimiento", native_enum=False))
    monto: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    referencia_tipo: Mapped[str | None] = mapped_column(String(50), nullable=True)
    referencia_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    nota: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    cuenta: Mapped["Cuenta"] = relationship(back_populates="movimientos")
