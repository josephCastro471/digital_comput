from datetime import date, datetime, time, timezone
from decimal import ROUND_HALF_UP, Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin
from app.database import get_db
from app.models.comision import ProveedorComision, TransaccionComision
from app.schemas.comision import (
    ComisionCalcularIn,
    ComisionCalculadaOut,
    ProveedorComisionOut,
    ProveedorComisionUpdate,
    TransaccionComisionCreate,
    TransaccionComisionOut,
)

router = APIRouter(prefix="/api/comisiones", tags=["comisiones"], dependencies=[Depends(get_current_admin)])

DOS_DECIMALES = Decimal("0.01")


def _get_proveedor_or_404(db: Session, proveedor_id: int) -> ProveedorComision:
    proveedor = db.get(ProveedorComision, proveedor_id)
    if proveedor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proveedor no encontrado")
    return proveedor


def _calcular(proveedor: ProveedorComision, valor_recibir: Decimal) -> dict:
    """valor_recibir es el neto que el negocio debe quedarse; se calcula el
    valor a cobrar al cliente de forma que, tras descontar la comision del
    proveedor (y el IVA sobre esa comision), quede exactamente valor_recibir."""
    comision_pct = proveedor.comision_pct / Decimal("100")
    iva_pct = proveedor.iva_pct / Decimal("100") if proveedor.aplica_iva else Decimal("0")

    denominador = Decimal("1") - comision_pct * (Decimal("1") + iva_pct)
    if denominador <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Configuracion de proveedor invalida: la comision combinada con el IVA es igual o mayor al 100%",
        )

    valor_cobrado_bruto = valor_recibir / denominador
    comision = (valor_cobrado_bruto * comision_pct).quantize(DOS_DECIMALES, rounding=ROUND_HALF_UP)

    iva_sobre_comision = Decimal("0.00")
    if proveedor.aplica_iva:
        iva_sobre_comision = (comision * iva_pct).quantize(DOS_DECIMALES, rounding=ROUND_HALF_UP)

    valor_cobrado = valor_recibir + comision + iva_sobre_comision
    return {
        "comision": comision,
        "iva_sobre_comision": iva_sobre_comision,
        "valor_cobrado": valor_cobrado,
    }


@router.get("/proveedores", response_model=list[ProveedorComisionOut])
def listar_proveedores(db: Session = Depends(get_db)):
    return db.scalars(select(ProveedorComision).order_by(ProveedorComision.nombre)).all()


@router.patch("/proveedores/{proveedor_id}", response_model=ProveedorComisionOut)
def actualizar_proveedor(proveedor_id: int, payload: ProveedorComisionUpdate, db: Session = Depends(get_db)):
    proveedor = _get_proveedor_or_404(db, proveedor_id)
    if payload.comision_pct is not None:
        proveedor.comision_pct = payload.comision_pct
    if payload.aplica_iva is not None:
        proveedor.aplica_iva = payload.aplica_iva
    if payload.iva_pct is not None:
        proveedor.iva_pct = payload.iva_pct
    db.commit()
    db.refresh(proveedor)
    return proveedor


@router.post("/calcular", response_model=ComisionCalculadaOut)
def calcular_comision(payload: ComisionCalcularIn, db: Session = Depends(get_db)):
    proveedor = _get_proveedor_or_404(db, payload.proveedor_id)
    resultado = _calcular(proveedor, payload.valor_recibir)
    return ComisionCalculadaOut(
        proveedor_id=proveedor.id,
        valor_recibir=payload.valor_recibir,
        **resultado,
    )


@router.post("/transacciones", response_model=TransaccionComisionOut, status_code=status.HTTP_201_CREATED)
def crear_transaccion(payload: TransaccionComisionCreate, db: Session = Depends(get_db)):
    proveedor = _get_proveedor_or_404(db, payload.proveedor_id)
    resultado = _calcular(proveedor, payload.valor_recibir)
    transaccion = TransaccionComision(
        proveedor_id=proveedor.id,
        valor_recibir=payload.valor_recibir,
        **resultado,
    )
    db.add(transaccion)
    db.commit()
    db.refresh(transaccion)
    return transaccion


@router.get("/transacciones", response_model=list[TransaccionComisionOut])
def listar_transacciones(fecha: date | None = None, db: Session = Depends(get_db)):
    query = select(TransaccionComision)
    if fecha is not None:
        inicio = datetime.combine(fecha, time.min, tzinfo=timezone.utc)
        fin = datetime.combine(fecha, time.max, tzinfo=timezone.utc)
        query = query.where(TransaccionComision.fecha.between(inicio, fin))
    query = query.order_by(TransaccionComision.fecha.desc())
    return db.scalars(query).all()
