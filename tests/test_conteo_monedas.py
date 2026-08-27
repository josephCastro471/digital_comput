from app.models.cuenta import Cuenta, TipoCuenta


def test_crear_conteo_calcula_total(client, auth_headers):
    response = client.post(
        "/api/conteo-monedas",
        json={"denominaciones": {"0.05": 50, "0.10": 27, "1.00": 3}, "nota": "cliente X"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["total"] == "8.20"
    assert body["denominaciones"] == {"0.05": 50, "0.10": 27, "1.00": 3}


def test_conteo_vacio_falla(client, auth_headers):
    response = client.post(
        "/api/conteo-monedas",
        json={"denominaciones": {}},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_conteo_denominacion_invalida_falla(client, auth_headers):
    response = client.post(
        "/api/conteo-monedas",
        json={"denominaciones": {"no-es-numero": 5}},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_conteo_no_crea_movimiento_cuenta(client, db_session, auth_headers):
    session = db_session()
    cuenta = Cuenta(nombre="Caja", tipo=TipoCuenta.EFECTIVO)
    session.add(cuenta)
    session.commit()
    session.close()

    client.post(
        "/api/conteo-monedas",
        json={"denominaciones": {"1.00": 10}},
        headers=auth_headers,
    )

    response = client.get("/api/cuentas/1", headers=auth_headers)
    assert response.json()["saldo_actual"] == "0.00"


def test_listar_conteos(client, auth_headers):
    client.post(
        "/api/conteo-monedas",
        json={"denominaciones": {"1.00": 1}},
        headers=auth_headers,
    )
    response = client.get("/api/conteo-monedas", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_conteo_requiere_auth(client):
    response = client.get("/api/conteo-monedas")
    assert response.status_code == 401
