from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin
from app.database import get_db
from app.models.inventario import Accesorio, MovimientoInventario
from app.schemas.inventario import (
    AccesorioCreate,
    AccesorioOut,
    AccesorioUpdate,
    MovimientoInventarioCreate,
    MovimientoInventarioOut,
)

router = APIRouter(prefix="/api/inventario", tags=["inventario"], dependencies=[Depends(get_current_admin)])


def _get_accesorio_or_404(db: Session, accesorio_id: int) -> Accesorio:
    accesorio = db.get(Accesorio, accesorio_id)
    if accesorio is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Accesorio no encontrado")
    return accesorio


@router.get("", response_model=list[AccesorioOut])
def listar_inventario(db: Session = Depends(get_db)):
    return db.scalars(select(Accesorio).order_by(Accesorio.nombre)).all()


@router.post("", response_model=AccesorioOut, status_code=status.HTTP_201_CREATED)
def crear_accesorio(payload: AccesorioCreate, db: Session = Depends(get_db)):
    accesorio = Accesorio(**payload.model_dump())
    db.add(accesorio)
    db.commit()
    db.refresh(accesorio)
    return accesorio


@router.patch("/{accesorio_id}", response_model=AccesorioOut)
def actualizar_accesorio(accesorio_id: int, payload: AccesorioUpdate, db: Session = Depends(get_db)):
    accesorio = _get_accesorio_or_404(db, accesorio_id)
    datos = payload.model_dump(exclude_unset=True)
    for campo, valor in datos.items():
        setattr(accesorio, campo, valor)
    db.commit()
    db.refresh(accesorio)
    return accesorio


@router.post(
    "/{accesorio_id}/movimiento",
    response_model=MovimientoInventarioOut,
    status_code=status.HTTP_201_CREATED,
)
def registrar_movimiento(accesorio_id: int, payload: MovimientoInventarioCreate, db: Session = Depends(get_db)):
    accesorio = _get_accesorio_or_404(db, accesorio_id)

    if payload.tipo == "salida" and payload.cantidad > accesorio.stock_actual:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stock insuficiente: hay {accesorio.stock_actual} y se pidieron {payload.cantidad}",
        )

    if payload.tipo == "entrada":
        accesorio.stock_actual += payload.cantidad
    else:
        accesorio.stock_actual -= payload.cantidad

    movimiento = MovimientoInventario(
        accesorio_id=accesorio.id,
        tipo=payload.tipo,
        cantidad=payload.cantidad,
        motivo=payload.motivo,
    )
    db.add(movimiento)
    db.commit()
    db.refresh(movimiento)
    return movimiento
