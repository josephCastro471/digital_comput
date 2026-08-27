from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.deps import get_current_admin
from app.database import get_db
from app.models.servicio import EscalonPrecio, Servicio, TipoPrecio
from app.schemas.servicio import ServicioCreate, ServicioOut, ServicioUpdate, validar_escalones

router = APIRouter(
    prefix="/api/servicios",
    tags=["servicios"],
    dependencies=[Depends(get_current_admin)],
)


def _get_servicio_or_404(db: Session, servicio_id: int) -> Servicio:
    servicio = db.get(Servicio, servicio_id)
    if servicio is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Servicio no encontrado")
    return servicio


def _escalones_orm(payload_escalones) -> list[EscalonPrecio]:
    return [
        EscalonPrecio(
            cantidad_desde=e.cantidad_desde,
            cantidad_hasta=e.cantidad_hasta,
            precio_unitario=e.precio_unitario,
        )
        for e in payload_escalones
    ]


@router.get("", response_model=list[ServicioOut])
def listar_servicios(db: Session = Depends(get_db)):
    return db.scalars(
        select(Servicio)
        .options(selectinload(Servicio.escalones))
        .order_by(Servicio.categoria, Servicio.nombre)
    ).all()


@router.post("", response_model=ServicioOut, status_code=status.HTTP_201_CREATED)
def crear_servicio(payload: ServicioCreate, db: Session = Depends(get_db)):
    servicio = Servicio(
        nombre=payload.nombre,
        categoria=payload.categoria,
        tipo_precio=payload.tipo_precio,
        precio_base=payload.precio_base,
        escalones=_escalones_orm(payload.escalones),
    )
    db.add(servicio)
    db.commit()
    db.refresh(servicio)
    return servicio


@router.patch("/{servicio_id}", response_model=ServicioOut)
def actualizar_servicio(servicio_id: int, payload: ServicioUpdate, db: Session = Depends(get_db)):
    servicio = _get_servicio_or_404(db, servicio_id)

    if payload.nombre is not None:
        servicio.nombre = payload.nombre
    if payload.categoria is not None:
        servicio.categoria = payload.categoria
    if payload.activo is not None:
        servicio.activo = payload.activo

    if payload.precio_base is not None:
        if servicio.tipo_precio == TipoPrecio.ESCALONADO:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="un servicio escalonado no usa precio_base",
            )
        servicio.precio_base = payload.precio_base

    if payload.escalones is not None:
        if servicio.tipo_precio != TipoPrecio.ESCALONADO:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="solo un servicio escalonado puede tener escalones",
            )
        if not payload.escalones:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="un servicio escalonado requiere al menos un escalon",
            )
        try:
            validar_escalones(payload.escalones)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        servicio.escalones = _escalones_orm(payload.escalones)

    db.commit()
    db.refresh(servicio)
    return servicio


@router.delete("/{servicio_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_servicio(servicio_id: int, db: Session = Depends(get_db)):
    servicio = _get_servicio_or_404(db, servicio_id)
    db.delete(servicio)
    db.commit()
