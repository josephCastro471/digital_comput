"""Seed de las 6 cuentas reales del negocio. Idempotente: no duplica si ya existen."""

from decimal import Decimal

from app.database import SessionLocal
from app.models.cuenta import Cuenta, TipoCuenta

CUENTAS_INICIALES = [
    {"nombre": "Caja", "tipo": TipoCuenta.EFECTIVO},
    {"nombre": "Pichincha", "tipo": TipoCuenta.CUPO_REVOLVENTE},
    {"nombre": "Guayaquil", "tipo": TipoCuenta.FONDO_FIJO},
    {"nombre": "Bolivariano", "tipo": TipoCuenta.FONDO_FIJO},
    {"nombre": "Pacífico", "tipo": TipoCuenta.FONDO_FIJO},
    {"nombre": "Fullcarga", "tipo": TipoCuenta.FONDO_FIJO},
]


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


if __name__ == "__main__":
    seed_cuentas()
