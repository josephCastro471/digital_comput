from decimal import Decimal

from app.models.comision import ProveedorComision


def _crear_proveedor(db_session, nombre="Payphone", comision_pct="3.50", aplica_iva=True, iva_pct="15.00"):
    session = db_session()
    proveedor = ProveedorComision(
        nombre=nombre,
        comision_pct=Decimal(comision_pct),
        aplica_iva=aplica_iva,
        iva_pct=Decimal(iva_pct),
    )
    session.add(proveedor)
    session.commit()
    session.refresh(proveedor)
    session.close()
    return proveedor.id


def test_calcular_comision_con_iva(client, db_session, auth_headers):
    proveedor_id = _crear_proveedor(db_session, comision_pct="3.50", aplica_iva=True, iva_pct="15.00")

    response = client.post(
        "/api/comisiones/calcular",
        json={"proveedor_id": proveedor_id, "valor_recibir": "100.00"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["comision"] == "3.65"
    assert body["iva_sobre_comision"] == "0.55"
    assert body["valor_cobrado"] == "104.20"


def test_calcular_comision_sin_iva(client, db_session, auth_headers):
    proveedor_id = _crear_proveedor(db_session, nombre="Deuna", comision_pct="2.00", aplica_iva=False, iva_pct="0")

    response = client.post(
        "/api/comisiones/calcular",
        json={"proveedor_id": proveedor_id, "valor_recibir": "50.00"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["comision"] == "1.02"
    assert body["iva_sobre_comision"] == "0.00"
    assert body["valor_cobrado"] == "51.02"


def test_calcular_payphone_caso_real(client, db_session, auth_headers):
    proveedor_id = _crear_proveedor(db_session, nombre="Payphone", comision_pct="5.00", aplica_iva=True, iva_pct="15.00")

    response = client.post(
        "/api/comisiones/calcular",
        json={"proveedor_id": proveedor_id, "valor_recibir": "50.00"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["comision"] == "2.65"
    assert body["iva_sobre_comision"] == "0.40"
    assert body["valor_cobrado"] == "53.05"


def test_calcular_deuna_caso_real(client, db_session, auth_headers):
    proveedor_id = _crear_proveedor(db_session, nombre="Deuna", comision_pct="4.00", aplica_iva=True, iva_pct="15.00")

    response = client.post(
        "/api/comisiones/calcular",
        json={"proveedor_id": proveedor_id, "valor_recibir": "48.00"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["comision"] == "2.01"
    assert body["iva_sobre_comision"] == "0.30"
    assert body["valor_cobrado"] == "50.31"


def test_calcular_no_persiste_transaccion(client, db_session, auth_headers):
    proveedor_id = _crear_proveedor(db_session)

    client.post(
        "/api/comisiones/calcular",
        json={"proveedor_id": proveedor_id, "valor_recibir": "100.00"},
        headers=auth_headers,
    )

    response = client.get("/api/comisiones/transacciones", headers=auth_headers)
    assert response.json() == []


def test_crear_transaccion_persiste(client, db_session, auth_headers):
    proveedor_id = _crear_proveedor(db_session, comision_pct="3.50", aplica_iva=True, iva_pct="15.00")

    response = client.post(
        "/api/comisiones/transacciones",
        json={"proveedor_id": proveedor_id, "valor_recibir": "100.00"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["valor_cobrado"] == "104.20"

    listado = client.get("/api/comisiones/transacciones", headers=auth_headers).json()
    assert len(listado) == 1
    assert listado[0]["id"] == body["id"]


def test_patch_proveedor_actualiza_porcentajes(client, db_session, auth_headers):
    proveedor_id = _crear_proveedor(db_session, comision_pct="0", aplica_iva=False, iva_pct="0")

    response = client.patch(
        f"/api/comisiones/proveedores/{proveedor_id}",
        json={"comision_pct": "4.00", "aplica_iva": True, "iva_pct": "15.00"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["comision_pct"] == "4.0000"
    assert body["aplica_iva"] is True
    assert body["iva_pct"] == "15.0000"


def test_listar_proveedores(client, db_session, auth_headers):
    _crear_proveedor(db_session, nombre="Payphone")
    _crear_proveedor(db_session, nombre="Deuna")

    response = client.get("/api/comisiones/proveedores", headers=auth_headers)
    assert response.status_code == 200
    assert {p["nombre"] for p in response.json()} == {"Payphone", "Deuna"}


def test_proveedor_inexistente_da_404(client, auth_headers):
    response = client.post(
        "/api/comisiones/calcular",
        json={"proveedor_id": 999, "valor_recibir": "10.00"},
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_comisiones_requiere_auth(client):
    response = client.get("/api/comisiones/proveedores")
    assert response.status_code == 401
