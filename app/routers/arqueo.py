from datetime import date, datetime, time, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.deps import get_current_admin
from app.database import get_db
from app.models.arqueo import ArqueoCaja, ArqueoDetalle, EstadoArqueo
from app.schemas.arqueo import ArqueoAbrirIn, ArqueoCajaOut, ArqueoCerrarIn

router = APIRouter(prefix="/api/arqueo", tags=["arqueo"], dependencies=[Depends(get_current_admin)])


def _get_arqueo_or_404(db: Session, arqueo_id: int) -> ArqueoCaja:
    arqueo = db.get(ArqueoCaja, arqueo_id)
    if arqueo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Arqueo no encontrado")
    return arqueo


@router.get("", response_model=list[ArqueoCajaOut])
def listar_arqueos(
    estado: EstadoArqueo | None = None,
    fecha: date | None = None,
    db: Session = Depends(get_db),
):
    query = select(ArqueoCaja).options(selectinload(ArqueoCaja.detalles))
    if estado is not None:
        query = query.where(ArqueoCaja.estado == estado)
    if fecha is not None:
        inicio = datetime.combine(fecha, time.min, tzinfo=timezone.utc)
        fin = datetime.combine(fecha, time.max, tzinfo=timezone.utc)
        query = query.where(ArqueoCaja.fecha_apertura.between(inicio, fin))
    query = query.order_by(ArqueoCaja.fecha_apertura.desc())
    return db.scalars(query).all()


@router.get("/{arqueo_id}", response_model=ArqueoCajaOut)
def obtener_arqueo(arqueo_id: int, db: Session = Depends(get_db)):
    return _get_arqueo_or_404(db, arqueo_id)


@router.post("/abrir", response_model=ArqueoCajaOut, status_code=status.HTTP_201_CREATED)
def abrir_arqueo(payload: ArqueoAbrirIn, db: Session = Depends(get_db)):
    abierto = db.scalar(select(ArqueoCaja).where(ArqueoCaja.estado == EstadoArqueo.ABIERTO))
    if abierto is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya hay un turno abierto (id={abierto.id}); cierralo antes de abrir otro",
        )
    arqueo = ArqueoCaja(saldo_apertura=payload.saldo_apertura, estado=EstadoArqueo.ABIERTO)
    db.add(arqueo)
    db.commit()
    db.refresh(arqueo)
    return arqueo


@router.post("/{arqueo_id}/cerrar", response_model=ArqueoCajaOut)
def cerrar_arqueo(arqueo_id: int, payload: ArqueoCerrarIn, db: Session = Depends(get_db)):
    arqueo = _get_arqueo_or_404(db, arqueo_id)
    if arqueo.estado != EstadoArqueo.ABIERTO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este arqueo ya esta cerrado",
        )

    detalles = []
    saldo_cierre = Decimal("0.00")
    for d in payload.detalles:
        subtotal = d.denominacion * d.cantidad
        saldo_cierre += subtotal
        detalles.append(ArqueoDetalle(denominacion=d.denominacion, cantidad=d.cantidad, subtotal=subtotal))

    arqueo.detalles = detalles
    arqueo.saldo_cierre = saldo_cierre
    arqueo.ganancia_neta = saldo_cierre - arqueo.saldo_apertura
    arqueo.fecha_cierre = datetime.now(timezone.utc)
    arqueo.estado = EstadoArqueo.CERRADO

    db.commit()
    db.refresh(arqueo)
    return arqueo
