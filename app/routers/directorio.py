from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin
from app.database import get_db
from app.models.directorio import Directorio
from app.schemas.directorio import DirectorioCreate, DirectorioOut, DirectorioUpdate

router = APIRouter(prefix="/api/directorio", tags=["directorio"], dependencies=[Depends(get_current_admin)])


def _get_directorio_or_404(db: Session, directorio_id: int) -> Directorio:
    entrada = db.get(Directorio, directorio_id)
    if entrada is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entrada de directorio no encontrada")
    return entrada


@router.get("", response_model=list[DirectorioOut])
def listar_directorio(buscar: str | None = None, db: Session = Depends(get_db)):
    query = select(Directorio)
    if buscar:
        patron = f"%{buscar}%"
        query = query.where(
            or_(
                Directorio.nombre.ilike(patron),
                Directorio.codigo.ilike(patron),
                Directorio.red.ilike(patron),
                Directorio.cedula_cuenta.ilike(patron),
                Directorio.nota.ilike(patron),
            )
        )
    query = query.order_by(Directorio.nombre)
    return db.scalars(query).all()


@router.post("", response_model=DirectorioOut, status_code=status.HTTP_201_CREATED)
def crear_directorio(payload: DirectorioCreate, db: Session = Depends(get_db)):
    entrada = Directorio(**payload.model_dump())
    db.add(entrada)
    db.commit()
    db.refresh(entrada)
    return entrada


@router.patch("/{directorio_id}", response_model=DirectorioOut)
def actualizar_directorio(directorio_id: int, payload: DirectorioUpdate, db: Session = Depends(get_db)):
    entrada = _get_directorio_or_404(db, directorio_id)
    datos = payload.model_dump(exclude_unset=True)
    for campo, valor in datos.items():
        setattr(entrada, campo, valor)
    db.commit()
    db.refresh(entrada)
    return entrada


@router.delete("/{directorio_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_directorio(directorio_id: int, db: Session = Depends(get_db)):
    entrada = _get_directorio_or_404(db, directorio_id)
    db.delete(entrada)
    db.commit()
