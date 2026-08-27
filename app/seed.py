"""Seed de datos reales del negocio (no ejemplos falsos). Idempotente: no duplica si ya existen."""

from decimal import Decimal

from app.database import SessionLocal
from app.models.comision import ProveedorComision
from app.models.cuenta import Cuenta, TipoCuenta

CUENTAS_INICIALES = [
    {"nombre": "Caja", "tipo": TipoCuenta.EFECTIVO},
    {"nombre": "Pichincha", "tipo": TipoCuenta.CUPO_REVOLVENTE},
    {"nombre": "Guayaquil", "tipo": TipoCuenta.FONDO_FIJO},
    {"nombre": "Bolivariano", "tipo": TipoCuenta.FONDO_FIJO},
    {"nombre": "Pacífico", "tipo": TipoCuenta.FONDO_FIJO},
    {"nombre": "Fullcarga", "tipo": TipoCuenta.FONDO_FIJO},
]

PROVEEDORES_COMISION_INICIALES = ["Payphone", "Deuna"]


def seed_cuentas() -> None:
    db = SessionLocal()
    try:
        existentes = {c.nombre for c in db.query(Cuenta).all()}
        creadas = []
        for datos in CUENTAS_INICIALES:
            if datos["nombre"] in existentes:
                continue
            cuenta = Cuenta(
                nombre=datos["nombre"],
                tipo=datos["tipo"],
                saldo_actual=Decimal("0.00"),
                saldo_inicial_dia=Decimal("0.00"),
            )
            db.add(cuenta)
            creadas.append(datos["nombre"])
        db.commit()
        if creadas:
            print(f"Cuentas creadas: {', '.join(creadas)}")
        else:
            print("Las 6 cuentas ya existian, no se creo nada.")
    finally:
        db.close()


def seed_proveedores_comision() -> None:
    """Crea Payphone y Deuna con comision_pct=0. No hay POST para proveedores en la
    API (regla dura: la config va en tabla, no en codigo) - configura los % reales
    despues via PATCH /api/comisiones/proveedores/{id}."""
    db = SessionLocal()
    try:
        existentes = {p.nombre for p in db.query(ProveedorComision).all()}
        creados = []
        for nombre in PROVEEDORES_COMISION_INICIALES:
            if nombre in existentes:
                continue
            db.add(
                ProveedorComision(
                    nombre=nombre,
                    comision_pct=Decimal("0.00"),
                    aplica_iva=False,
                    iva_pct=Decimal("0.00"),
                )
            )
            creados.append(nombre)
        db.commit()
        if creados:
            print(
                f"Proveedores de comision creados: {', '.join(creados)} "
                "(configura sus % reales via PATCH /api/comisiones/proveedores/{id})"
            )
        else:
            print("Los proveedores de comision ya existian, no se creo nada.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_cuentas()
    seed_proveedores_comision()
