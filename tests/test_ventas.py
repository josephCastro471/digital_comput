from decimal import Decimal

from app.models.cuenta import Cuenta, TipoCuenta
from app.models.servicio import EscalonPrecio, Servicio, TipoPrecio


def _crear_servicio_fijo(db_session, precio="0.10"):
    session = db_session()
    servicio = Servicio(
        nombre="Impresion B/N", categoria="impresiones", tipo_precio=TipoPrecio.FIJO, precio_base=Decimal(precio)
    )
    session.add(servicio)
    session.commit()
    session.refresh(servicio)
    session.close()
    return servicio.id


def _crear_servicio_variable(db_session):
    session = db_session()
    servicio = Servicio(nombre="Reparacion", categoria="tecnico", tipo_precio=TipoPrecio.VARIABLE)
    session.add(servicio)
    session.commit()
    session.refresh(servicio)
    session.close()
    return servicio.id


def _crear_servicio_escalonado(db_session):
    session = db_session()
    servicio = Servicio(nombre="Copias", categoria="impresiones", tipo_precio=TipoPrecio.ESCALONADO)
    servicio.escalones = [
        EscalonPrecio(cantidad_desde=1, cantidad_hasta=10, precio_unitario=Decimal("0.10")),
        EscalonPrecio(cantidad_desde=11, cantidad_hasta=None, precio_unitario=Decimal("0.08")),
    ]
    session.add(servicio)
    session.commit()
    session.refresh(servicio)
    session.close()
    return servicio.id


def _crear_cuenta(db_session, nombre="Caja", tipo=TipoCuenta.EFECTIVO):
    session = db_session()
    cuenta = Cuenta(nombre=nombre, tipo=tipo)
    session.add(cuenta)
    session.commit()
    session.refresh(cuenta)
    session.close()
    return cuenta.id


def test_venta_servicio_fijo_calcula_total(client, db_session, auth_headers):
    servicio_id = _crear_servicio_fijo(db_session, "0.10")

    response = client.post(
        "/api/ventas",
        json={"items": [{"servicio_id": servicio_id, "cantidad": 5}]},
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["total"] == "0.50"
    assert body["items"][0]["precio_unitario"] == "0.10"
    assert body["items"][0]["subtotal"] == "0.50"


def test_venta_servicio_variable_requiere_precio(client, db_session, auth_headers):
    servicio_id = _crear_servicio_variable(db_session)

    response = client.post(
        "/api/ventas",
        json={"items": [{"servicio_id": servicio_id, "cantidad": 1}]},
        headers=auth_headers,
    )
    assert response.status_code == 400

    response = client.post(
        "/api/ventas",
        json={"items": [{"servicio_id": servicio_id, "cantidad": 1, "precio_unitario": "15.00"}]},
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["total"] == "15.00"


def test_venta_servicio_escalonado_usa_tramo_correcto(client, db_session, auth_headers):
    servicio_id = _crear_servicio_escalonado(db_session)

    response = client.post(
        "/api/ventas",
        json={"items": [{"servicio_id": servicio_id, "cantidad": 15}]},
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["items"][0]["precio_unitario"] == "0.08"
    assert body["total"] == "1.20"


def test_venta_con_cuenta_genera_deposito(client, db_session, auth_headers):
    servicio_id = _crear_servicio_fijo(db_session, "1.00")
    cuenta_id = _crear_cuenta(db_session)

    response = client.post(
        "/api/ventas",
        json={"cuenta_id": cuenta_id, "items": [{"servicio_id": servicio_id, "cantidad": 3}]},
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["total"] == "3.00"

    cuenta_response = client.get(f"/api/cuentas/{cuenta_id}", headers=auth_headers).json()
    assert cuenta_response["saldo_actual"] == "3.00"

    movimientos = client.get(f"/api/cuentas/{cuenta_id}/movimientos", headers=auth_headers).json()
    assert len(movimientos) == 1
    assert movimientos[0]["tipo"] == "deposito"
    assert movimientos[0]["monto"] == "3.00"
    assert movimientos[0]["referencia_tipo"] == "venta"


def test_venta_sin_cuenta_no_toca_saldos(client, db_session, auth_headers):
    servicio_id = _crear_servicio_fijo(db_session, "1.00")
    cuenta_id = _crear_cuenta(db_session)

    client.post(
        "/api/ventas",
        json={"items": [{"servicio_id": servicio_id, "cantidad": 1}]},
        headers=auth_headers,
    )

    cuenta_response = client.get(f"/api/cuentas/{cuenta_id}", headers=auth_headers).json()
    assert cuenta_response["saldo_actual"] == "0.00"


def test_venta_servicio_inexistente_da_404(client, auth_headers):
    response = client.post(
        "/api/ventas",
        json={"items": [{"servicio_id": 999, "cantidad": 1}]},
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_venta_servicio_inactivo_falla(client, db_session, auth_headers):
    servicio_id = _crear_servicio_fijo(db_session, "1.00")
    session = db_session()
    servicio = session.get(Servicio, servicio_id)
    servicio.activo = False
    session.commit()
    session.close()

    response = client.post(
        "/api/ventas",
        json={"items": [{"servicio_id": servicio_id, "cantidad": 1}]},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_venta_multiples_items_suma_total(client, db_session, auth_headers):
    fijo_id = _crear_servicio_fijo(db_session, "0.50")
    variable_id = _crear_servicio_variable(db_session)

    response = client.post(
        "/api/ventas",
        json={
            "items": [
                {"servicio_id": fijo_id, "cantidad": 2},
                {"servicio_id": variable_id, "cantidad": 1, "precio_unitario": "10.00"},
            ]
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["total"] == "11.00"


def test_listar_ventas(client, db_session, auth_headers):
    servicio_id = _crear_servicio_fijo(db_session, "1.00")
    client.post(
        "/api/ventas",
        json={"items": [{"servicio_id": servicio_id, "cantidad": 1}]},
        headers=auth_headers,
    )

    response = client.get("/api/ventas", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_venta_requiere_auth(client):
    response = client.get("/api/ventas")
    assert response.status_code == 401
