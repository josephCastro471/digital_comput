from decimal import Decimal

from app.models.cuenta import Cuenta, TipoCuenta


def _crear_cuenta(db_session, **kwargs):
    session = db_session()
    cuenta = Cuenta(
        nombre=kwargs.get("nombre", "Caja"),
        tipo=kwargs.get("tipo", TipoCuenta.EFECTIVO),
        saldo_actual=kwargs.get("saldo_actual", Decimal("0.00")),
        saldo_inicial_dia=kwargs.get("saldo_inicial_dia", Decimal("0.00")),
        cupo_transaccional=kwargs.get("cupo_transaccional"),
    )
    session.add(cuenta)
    session.commit()
    session.refresh(cuenta)
    session.close()
    return cuenta.id


def test_listar_cuentas_requiere_auth(client):
    response = client.get("/api/cuentas")
    assert response.status_code == 401


def test_listar_cuentas_vacio(client, auth_headers):
    response = client.get("/api/cuentas", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_crear_movimiento_deposito_actualiza_saldo(client, db_session, auth_headers):
    cuenta_id = _crear_cuenta(db_session, nombre="Caja", tipo=TipoCuenta.EFECTIVO)

    response = client.post(
        f"/api/cuentas/{cuenta_id}/movimientos",
        json={"tipo": "deposito", "monto": "50.00"},
        headers=auth_headers,
    )
    assert response.status_code == 201

    cuenta_response = client.get(f"/api/cuentas/{cuenta_id}", headers=auth_headers)
    assert cuenta_response.json()["saldo_actual"] == "50.00"


def test_uso_solo_aplica_a_cupo_revolvente(client, db_session, auth_headers):
    cuenta_id = _crear_cuenta(db_session, nombre="Caja", tipo=TipoCuenta.EFECTIVO)

    response = client.post(
        f"/api/cuentas/{cuenta_id}/movimientos",
        json={"tipo": "uso", "monto": "10.00"},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_uso_actualiza_cupo_utilizado(client, db_session, auth_headers):
    cuenta_id = _crear_cuenta(
        db_session,
        nombre="Pichincha",
        tipo=TipoCuenta.CUPO_REVOLVENTE,
        cupo_transaccional=Decimal("500.00"),
    )

    response = client.post(
        f"/api/cuentas/{cuenta_id}/movimientos",
        json={"tipo": "uso", "monto": "100.00"},
        headers=auth_headers,
    )
    assert response.status_code == 201

    cuenta_response = client.get(f"/api/cuentas/{cuenta_id}", headers=auth_headers).json()
    assert cuenta_response["cupo_utilizado"] == "100.00"
    assert cuenta_response["cupo_disponible"] == "400.00"


def test_patch_cupo_solo_cupo_revolvente(client, db_session, auth_headers):
    cuenta_id = _crear_cuenta(db_session, nombre="Caja", tipo=TipoCuenta.EFECTIVO)

    response = client.patch(
        f"/api/cuentas/{cuenta_id}/cupo",
        json={"cupo_transaccional": "1000.00"},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_patch_cupo_actualiza_pichincha(client, db_session, auth_headers):
    cuenta_id = _crear_cuenta(db_session, nombre="Pichincha", tipo=TipoCuenta.CUPO_REVOLVENTE)

    response = client.patch(
        f"/api/cuentas/{cuenta_id}/cupo",
        json={"cupo_transaccional": "800.00"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["cupo_transaccional"] == "800.00"


def test_movimiento_ajuste_permite_negativo(client, db_session, auth_headers):
    cuenta_id = _crear_cuenta(
        db_session, nombre="Caja", tipo=TipoCuenta.EFECTIVO, saldo_actual=Decimal("100.00")
    )

    response = client.post(
        f"/api/cuentas/{cuenta_id}/movimientos",
        json={"tipo": "ajuste", "monto": "-20.00", "nota": "correccion"},
        headers=auth_headers,
    )
    assert response.status_code == 201

    cuenta_response = client.get(f"/api/cuentas/{cuenta_id}", headers=auth_headers).json()
    assert cuenta_response["saldo_actual"] == "80.00"


def test_movimiento_negativo_rechazado_fuera_de_ajuste(client, db_session, auth_headers):
    cuenta_id = _crear_cuenta(db_session, nombre="Caja", tipo=TipoCuenta.EFECTIVO)

    response = client.post(
        f"/api/cuentas/{cuenta_id}/movimientos",
        json={"tipo": "deposito", "monto": "-5.00"},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_cuenta_inexistente_da_404(client, auth_headers):
    response = client.get("/api/cuentas/999", headers=auth_headers)
    assert response.status_code == 404


def test_cuadre_solo_fondo_fijo(client, db_session, auth_headers):
    cuenta_id = _crear_cuenta(db_session, nombre="Caja", tipo=TipoCuenta.EFECTIVO)

    response = client.post(
        f"/api/cuentas/{cuenta_id}/cuadre",
        json={"valor_actual": "100.00"},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_cuadre_retirando_todo_caso_real_bolivariano(client, db_session, auth_headers):
    cuenta_id = _crear_cuenta(
        db_session,
        nombre="Bolivariano",
        tipo=TipoCuenta.FONDO_FIJO,
        saldo_actual=Decimal("323.54"),
        saldo_inicial_dia=Decimal("323.54"),
    )

    response = client.post(
        f"/api/cuentas/{cuenta_id}/cuadre",
        json={"valor_actual": "92.34"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["recaudado"] == "231.20"
    assert body["valor_inicial"] == "323.54"
    assert body["valor_actual"] == "92.34"
    assert body["cuenta"]["saldo_actual"] == "92.34"
    assert body["cuenta"]["saldo_inicial_dia"] == "92.34"


def test_cuadre_retiro_parcial_caso_real_fullcarga(client, db_session, auth_headers):
    cuenta_id = _crear_cuenta(
        db_session,
        nombre="Fullcarga",
        tipo=TipoCuenta.FONDO_FIJO,
        saldo_actual=Decimal("290.00"),
        saldo_inicial_dia=Decimal("290.00"),
    )

    # Recauda 14.65 (290 - 275.35 en el banco) pero solo retira 10, dejando
    # 280 como lo que decide que queda guardado en el fondo.
    response = client.post(
        f"/api/cuentas/{cuenta_id}/cuadre",
        json={"valor_actual": "280.00"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["recaudado"] == "10.00"
    assert body["valor_actual"] == "280.00"
    assert body["cuenta"]["saldo_actual"] == "280.00"
    assert body["cuenta"]["saldo_inicial_dia"] == "280.00"


def test_cuadre_persiste_como_valor_inicial_del_proximo(client, db_session, auth_headers):
    cuenta_id = _crear_cuenta(
        db_session,
        nombre="Fullcarga",
        tipo=TipoCuenta.FONDO_FIJO,
        saldo_actual=Decimal("290.00"),
        saldo_inicial_dia=Decimal("290.00"),
    )

    client.post(
        f"/api/cuentas/{cuenta_id}/cuadre",
        json={"valor_actual": "280.00"},
        headers=auth_headers,
    )

    response = client.post(
        f"/api/cuentas/{cuenta_id}/cuadre",
        json={"valor_actual": "265.00"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["valor_inicial"] == "280.00"
    assert body["recaudado"] == "15.00"


def test_cuadre_sin_drift_no_crea_movimiento(client, db_session, auth_headers):
    cuenta_id = _crear_cuenta(
        db_session,
        nombre="Bolivariano",
        tipo=TipoCuenta.FONDO_FIJO,
        saldo_actual=Decimal("50.00"),
        saldo_inicial_dia=Decimal("50.00"),
    )

    response = client.post(
        f"/api/cuentas/{cuenta_id}/cuadre",
        json={"valor_actual": "50.00"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["recaudado"] == "0.00"

    movimientos = client.get(f"/api/cuentas/{cuenta_id}/movimientos", headers=auth_headers).json()
    assert movimientos == []
