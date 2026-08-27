from datetime import date, datetime, time, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin
from app.database import get_db
from app.models.conteo_monedas import ConteoMonedas
from app.schemas.conteo_monedas import ConteoMonedasCreate, ConteoMonedasOut

router = APIRouter(
    prefix="/api/conteo-monedas",
    tags=["conteo-monedas"],
    dependencies=[Depends(get_current_admin)],
)


@router.post("", response_model=ConteoMonedasOut, status_code=status.HTTP_201_CREATED)
def crear_conteo(payload: ConteoMonedasCreate, db: Session = Depends(get_db)):
    total = sum(
        (Decimal(clave) * cantidad for clave, cantidad in payload.denominaciones.items()),
        start=Decimal("0.00"),
    )
    conteo = ConteoMonedas(denominaciones=payload.denominaciones, total=total, nota=payload.nota)
    db.add(conteo)
    db.commit()
    db.refresh(conteo)
    return conteo


@router.get("", response_model=list[ConteoMonedasOut])
def listar_conteos(fecha: date | None = None, db: Session = Depends(get_db)):
    query = select(ConteoMonedas)
    if fecha is not None:
        inicio = datetime.combine(fecha, time.min, tzinfo=timezone.utc)
        fin = datetime.combine(fecha, time.max, tzinfo=timezone.utc)
        query = query.where(ConteoMonedas.fecha.between(inicio, fin))
    query = query.order_by(ConteoMonedas.fecha.desc())
    return db.scalars(query).all()
