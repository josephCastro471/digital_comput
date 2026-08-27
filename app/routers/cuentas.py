from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin
from app.database import get_db
from app.models.cuenta import Cuenta, MovimientoCuenta, TipoCuenta, TipoMovimiento
from app.schemas.cuenta import (
    CuentaCierreDiaOut,
    CuentaCupoUpdate,
    CuentaOut,
    CuentaSaldoDiaIn,
    MovimientoCuentaCreate,
    MovimientoCuentaOut,
)

router = APIRouter(
    prefix="/api/cuentas",
    tags=["cuentas"],
    dependencies=[Depends(get_current_admin)],
)


def _get_cuenta_or_404(db: Session, cuenta_id: int) -> Cuenta:
    cuenta = db.get(Cuenta, cuenta_id)
    if cuenta is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta no encontrada")
    return cuenta


def aplicar_movimiento(cuenta: Cuenta, tipo: TipoMovimiento, monto) -> None:
    """Aplica el efecto de un movimiento sobre saldo_actual/cupo_utilizado.

    Compartido con el router de ventas para no duplicar esta logica al
    generar el deposito automatico de una venta cobrada a una cuenta.
    """
    if tipo == TipoMovimiento.USO:
        cuenta.cupo_utilizado += monto
    elif tipo == TipoMovimiento.DEPOSITO:
        cuenta.saldo_actual += monto
    elif tipo == TipoMovimiento.RETIRO:
        cuenta.saldo_actual -= monto
    elif tipo == TipoMovimiento.AJUSTE:
        cuenta.saldo_actual += monto


@router.get("", response_model=list[CuentaOut])
def listar_cuentas(db: Session = Depends(get_db)):
    return db.scalars(select(Cuenta).order_by(Cuenta.nombre)).all()


@router.get("/{cuenta_id}", response_model=CuentaOut)
def obtener_cuenta(cuenta_id: int, db: Session = Depends(get_db)):
    return _get_cuenta_or_404(db, cuenta_id)


@router.get("/{cuenta_id}/movimientos", response_model=list[MovimientoCuentaOut])
def listar_movimientos(cuenta_id: int, db: Session = Depends(get_db)):
    _get_cuenta_or_404(db, cuenta_id)
    return db.scalars(
        select(MovimientoCuenta)
        .where(MovimientoCuenta.cuenta_id == cuenta_id)
        .order_by(MovimientoCuenta.fecha.desc())
    ).all()


@router.post("/{cuenta_id}/movimientos", response_model=MovimientoCuentaOut, status_code=status.HTTP_201_CREATED)
def crear_movimiento(cuenta_id: int, payload: MovimientoCuentaCreate, db: Session = Depends(get_db)):
    cuenta = _get_cuenta_or_404(db, cuenta_id)

    if payload.tipo == TipoMovimiento.USO and cuenta.tipo != TipoCuenta.CUPO_REVOLVENTE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El movimiento 'uso' solo aplica a cuentas de tipo cupo_revolvente",
        )

    aplicar_movimiento(cuenta, payload.tipo, payload.monto)

    movimiento = MovimientoCuenta(
        cuenta_id=cuenta.id,
        tipo=payload.tipo,
        monto=payload.monto,
        referencia_tipo=payload.referencia_tipo,
        referencia_id=payload.referencia_id,
        nota=payload.nota,
    )
    db.add(movimiento)
    db.commit()
    db.refresh(movimiento)
    return movimiento


def _sincronizar_saldo(cuenta: Cuenta, db: Session, saldo_real, nota: str, referencia_tipo: str) -> None:
    """Crea un movimiento de ajuste que corrige saldo_actual para que coincida
    con el valor real ingresado (ej. el saldo bancario verificado a mano). No
    crea nada si ya coinciden, para no ensuciar el historial con ajustes de 0."""
    delta = saldo_real - cuenta.saldo_actual
    if delta == 0:
        return
    aplicar_movimiento(cuenta, TipoMovimiento.AJUSTE, delta)
    db.add(
        MovimientoCuenta(
            cuenta_id=cuenta.id,
            tipo=TipoMovimiento.AJUSTE,
            monto=delta,
            referencia_tipo=referencia_tipo,
            nota=nota,
        )
    )


@router.post("/{cuenta_id}/iniciar-dia", response_model=CuentaOut)
def iniciar_dia(cuenta_id: int, payload: CuentaSaldoDiaIn, db: Session = Depends(get_db)):
    cuenta = _get_cuenta_or_404(db, cuenta_id)
    if cuenta.tipo != TipoCuenta.FONDO_FIJO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Iniciar/cerrar dia solo aplica a cuentas de tipo fondo_fijo",
        )

    _sincronizar_saldo(
        cuenta, db, payload.saldo, "Saldo verificado al iniciar el dia", "inicio_dia"
    )
    cuenta.saldo_inicial_dia = payload.saldo
    db.commit()
    db.refresh(cuenta)
    return cuenta


@router.post("/{cuenta_id}/cerrar-dia", response_model=CuentaCierreDiaOut)
def cerrar_dia(cuenta_id: int, payload: CuentaSaldoDiaIn, db: Session = Depends(get_db)):
    cuenta = _get_cuenta_or_404(db, cuenta_id)
    if cuenta.tipo != TipoCuenta.FONDO_FIJO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Iniciar/cerrar dia solo aplica a cuentas de tipo fondo_fijo",
        )

    recaudado = cuenta.saldo_inicial_dia - payload.saldo
    _sincronizar_saldo(
        cuenta,
        db,
        payload.saldo,
        f"Cuadre de fondo: recaudado {recaudado}",
        "cuadre_fondo",
    )
    db.commit()
    db.refresh(cuenta)
    return CuentaCierreDiaOut(
        recaudado=recaudado,
        saldo_inicial_dia=cuenta.saldo_inicial_dia,
        saldo_final=payload.saldo,
        cuenta=cuenta,
    )


@router.patch("/{cuenta_id}/cupo", response_model=CuentaOut)
def actualizar_cupo(cuenta_id: int, payload: CuentaCupoUpdate, db: Session = Depends(get_db)):
    cuenta = _get_cuenta_or_404(db, cuenta_id)
    if cuenta.tipo != TipoCuenta.CUPO_REVOLVENTE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo las cuentas de tipo cupo_revolvente tienen cupo transaccional",
        )
    cuenta.cupo_transaccional = payload.cupo_transaccional
    db.commit()
    db.refresh(cuenta)
    return cuenta
