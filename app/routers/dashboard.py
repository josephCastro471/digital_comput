from datetime import date, datetime, time, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.deps import get_current_admin
from app.database import get_db
from app.models.arqueo import ArqueoCaja
from app.models.comision import TransaccionComision
from app.models.cuenta import Cuenta
from app.models.venta import Venta
from app.schemas.dashboard import (
    ComisionesResumen,
    DashboardRangoOut,
    DashboardResumenOut,
    VentasResumen,
)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"], dependencies=[Depends(get_current_admin)])

DOS_DECIMALES = Decimal("0.01")


def _to_decimal(valor) -> Decimal:
    if not isinstance(valor, Decimal):
        valor = Decimal(str(valor))
    return valor.quantize(DOS_DECIMALES)


def _rango_utc(desde: date, hasta: date) -> tuple[datetime, datetime]:
    inicio = datetime.combine(desde, time.min, tzinfo=timezone.utc)
    fin = datetime.combine(hasta, time.max, tzinfo=timezone.utc)
    return inicio, fin


def _resumen_ventas(db: Session, inicio: datetime, fin: datetime) -> VentasResumen:
    cantidad, total = db.execute(
        select(func.count(Venta.id), func.coalesce(func.sum(Venta.total), 0)).where(
            Venta.fecha.between(inicio, fin)
        )
    ).one()
    return VentasResumen(cantidad=cantidad, total=_to_decimal(total))


def _resumen_comisiones(db: Session, inicio: datetime, fin: datetime) -> ComisionesResumen:
    cantidad, total_comision, total_iva, total_cobrado = db.execute(
        select(
            func.count(TransaccionComision.id),
            func.coalesce(func.sum(TransaccionComision.comision), 0),
            func.coalesce(func.sum(TransaccionComision.iva_sobre_comision), 0),
            func.coalesce(func.sum(TransaccionComision.valor_cobrado), 0),
        ).where(TransaccionComision.fecha.between(inicio, fin))
    ).one()
    return ComisionesResumen(
        cantidad=cantidad,
        total_comision=_to_decimal(total_comision),
        total_iva_sobre_comision=_to_decimal(total_iva),
        total_valor_cobrado=_to_decimal(total_cobrado),
    )


def _arqueos_en_rango(db: Session, inicio: datetime, fin: datetime):
    return db.scalars(
        select(ArqueoCaja)
        .options(selectinload(ArqueoCaja.detalles))
        .where(ArqueoCaja.fecha_apertura.between(inicio, fin))
        .order_by(ArqueoCaja.fecha_apertura)
    ).all()


def _cuentas_actuales(db: Session):
    return db.scalars(select(Cuenta).order_by(Cuenta.nombre)).all()


@router.get("/resumen", response_model=DashboardResumenOut)
def resumen(fecha: date, db: Session = Depends(get_db)):
    inicio, fin = _rango_utc(fecha, fecha)
    return DashboardResumenOut(
        fecha=fecha,
        ventas=_resumen_ventas(db, inicio, fin),
        comisiones=_resumen_comisiones(db, inicio, fin),
        arqueos=_arqueos_en_rango(db, inicio, fin),
        cuentas=_cuentas_actuales(db),
    )


@router.get("/rango", response_model=DashboardRangoOut)
def rango(desde: date, hasta: date, db: Session = Depends(get_db)):
    if hasta < desde:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="'hasta' no puede ser anterior a 'desde'",
        )
    inicio, fin = _rango_utc(desde, hasta)
    return DashboardRangoOut(
        desde=desde,
        hasta=hasta,
        ventas=_resumen_ventas(db, inicio, fin),
        comisiones=_resumen_comisiones(db, inicio, fin),
        arqueos=_arqueos_en_rango(db, inicio, fin),
        cuentas=_cuentas_actuales(db),
    )
