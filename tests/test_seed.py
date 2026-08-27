import app.seed as seed_module
from app.models.comision import ProveedorComision
from app.models.cuenta import Cuenta, TipoCuenta
from app.seed import (
    CUENTAS_INICIALES,
    PROVEEDORES_COMISION_INICIALES,
    seed_cuentas,
    seed_proveedores_comision,
)


def test_seed_crea_las_6_cuentas(db_session, monkeypatch):
    monkeypatch.setattr(seed_module, "SessionLocal", db_session)

    seed_cuentas()

    session = db_session()
    cuentas = session.query(Cuenta).all()
    session.close()

    assert len(cuentas) == 6
    assert {c.nombre for c in cuentas} == {c["nombre"] for c in CUENTAS_INICIALES}

    pichincha = next(c for c in cuentas if c.nombre == "Pichincha")
    assert pichincha.tipo == TipoCuenta.CUPO_REVOLVENTE


def test_seed_es_idempotente(db_session, monkeypatch):
    monkeypatch.setattr(seed_module, "SessionLocal", db_session)

    seed_cuentas()
    seed_cuentas()

    session = db_session()
    cuentas = session.query(Cuenta).all()
    session.close()

    assert len(cuentas) == 6


def test_seed_crea_los_proveedores_de_comision(db_session, monkeypatch):
    monkeypatch.setattr(seed_module, "SessionLocal", db_session)

    seed_proveedores_comision()

    session = db_session()
    proveedores = session.query(ProveedorComision).all()
    session.close()

    assert {p.nombre for p in proveedores} == {d["nombre"] for d in PROVEEDORES_COMISION_INICIALES}

    payphone = next(p for p in proveedores if p.nombre == "Payphone")
    assert payphone.comision_pct == 5
    assert payphone.aplica_iva is True
    assert payphone.iva_pct == 15

    deuna = next(p for p in proveedores if p.nombre == "Deuna")
    assert deuna.comision_pct == 4
    assert deuna.aplica_iva is True
    assert deuna.iva_pct == 15


def test_seed_proveedores_es_idempotente(db_session, monkeypatch):
    monkeypatch.setattr(seed_module, "SessionLocal", db_session)

    seed_proveedores_comision()
    seed_proveedores_comision()

    session = db_session()
    proveedores = session.query(ProveedorComision).all()
    session.close()

    assert len(proveedores) == 2
