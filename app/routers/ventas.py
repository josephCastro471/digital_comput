from datetime import date, datetime, time, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.deps import get_current_admin
from app.database import get_db
from app.models.cuenta import Cuenta, MovimientoCuenta, TipoMovimiento
from app.models.servicio import Servicio, TipoPrecio
from app.models.venta import Venta, VentaItem
from app.routers.cuentas import aplicar_movimiento
from app.schemas.venta import VentaCreate, VentaOut

router = APIRouter(prefix="/api/ventas", tags=["ventas"], dependencies=[Depends(get_current_admin)])


def _get_venta_or_404(db: Session, venta_id: int) -> Venta:
    venta = db.get(Venta, venta_id)
    if venta is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venta no encontrada")
    return venta


def _precio_para_item(servicio: Servicio, cantidad: int, precio_unitario_in: Decimal | None) -> Decimal:
    if servicio.tipo_precio == TipoPrecio.FIJO:
        return servicio.precio_base

    if servicio.tipo_precio == TipoPrecio.VARIABLE:
        if precio_unitario_in is None or precio_unitario_in <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El servicio '{servicio.nombre}' es de precio variable: precio_unitario es obligatorio",
            )
        return precio_unitario_in

    # ESCALONADO: la relacion ya viene ordenada por cantidad_desde
    for escalon in servicio.escalones:
        dentro_del_rango = escalon.cantidad_desde <= cantidad and (
            escalon.cantidad_hasta is None or cantidad <= escalon.cantidad_hasta
        )
        if dentro_del_rango:
            return escalon.precio_unitario

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"El servicio '{servicio.nombre}' no tiene un escalon de precio para cantidad={cantidad}",
    )


@router.get("", response_model=list[VentaOut])
def listar_ventas(fecha: date | None = None, db: Session = Depends(get_db)):
    query = select(Venta).options(selectinload(Venta.items))
    if fecha is not None:
        inicio = datetime.combine(fecha, time.min, tzinfo=timezone.utc)
        fin = datetime.combine(fecha, time.max, tzinfo=timezone.utc)
        query = query.where(Venta.fecha.between(inicio, fin))
    query = query.order_by(Venta.fecha.desc())
    return db.scalars(query).all()


@router.get("/{venta_id}", response_model=VentaOut)
def obtener_venta(venta_id: int, db: Session = Depends(get_db)):
    return _get_venta_or_404(db, venta_id)


@router.post("", response_model=VentaOut, status_code=status.HTTP_201_CREATED)
def crear_venta(payload: VentaCreate, db: Session = Depends(get_db)):
    cuenta = None
    if payload.cuenta_id is not None:
        cuenta = db.get(Cuenta, payload.cuenta_id)
        if cuenta is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta no encontrada")
        if not cuenta.activa:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La cuenta no esta activa")

    venta_items = []
    total = Decimal("0.00")

    for item in payload.items:
        servicio = db.get(Servicio, item.servicio_id)
        if servicio is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Servicio {item.servicio_id} no encontrado",
            )
        if not servicio.activo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El servicio '{servicio.nombre}' no esta activo",
            )

        precio_unitario = _precio_para_item(servicio, item.cantidad, item.precio_unitario)
        subtotal = precio_unitario * item.cantidad
        total += subtotal

        venta_items.append(
            VentaItem(
                servicio_id=servicio.id,
                cantidad=item.cantidad,
                precio_unitario=precio_unitario,
                subtotal=subtotal,
            )
        )

    venta = Venta(cuenta_id=payload.cuenta_id, total=total, items=venta_items)
    db.add(venta)
    db.flush()

    if cuenta is not None:
        aplicar_movimiento(cuenta, TipoMovimiento.DEPOSITO, total)
        db.add(
            MovimientoCuenta(
                cuenta_id=cuenta.id,
                tipo=TipoMovimiento.DEPOSITO,
                monto=total,
                referencia_tipo="venta",
                referencia_id=venta.id,
                nota=f"Venta #{venta.id}",
            )
        )

    db.commit()
    db.refresh(venta)
    return venta
