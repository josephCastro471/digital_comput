import app.seed as seed_module
from app.models.cuenta import Cuenta, TipoCuenta
from app.seed import CUENTAS_INICIALES, seed_cuentas


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
