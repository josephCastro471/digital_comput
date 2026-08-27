from datetime import date
from decimal import Decimal

from app.models.comision import ProveedorComision
from app.models.cuenta import Cuenta, TipoCuenta
from app.models.servicio import Servicio, TipoPrecio


def _crear_cuenta(db_session, nombre="Caja"):
    session = db_session()
    cuenta = Cuenta(nombre=nombre, tipo=TipoCuenta.EFECTIVO)
    session.add(cuenta)
    session.commit()
    session.refresh(cuenta)
    session.close()
    return cuenta.id


def _crear_servicio(db_session, precio="1.00"):
    session = db_session()
    servicio = Servicio(
        nombre="Impresion", categoria="impresiones", tipo_precio=TipoPrecio.FIJO, precio_base=Decimal(precio)
    )
    session.add(servicio)
    session.commit()
    session.refresh(servicio)
    session.close()
    return servicio.id


def _crear_proveedor(db_session):
    session = db_session()
    proveedor = ProveedorComision(
        nombre="Payphone", comision_pct=Decimal("3.50"), aplica_iva=True, iva_pct=Decimal("15.00")
    )
    session.add(proveedor)
    session.commit()
    session.refresh(proveedor)
    session.close()
    return proveedor.id


def test_resumen_dia_sin_datos(client, auth_headers):
    response = client.get("/api/dashboard/resumen?fecha=2026-08-27", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["ventas"] == {"cantidad": 0, "total": "0.00"}
    assert body["comisiones"]["cantidad"] == 0
    assert body["arqueos"] == []


def test_resumen_incluye_cuentas_actuales(client, db_session, auth_headers):
    _crear_cuenta(db_session, "Caja")

    response = client.get("/api/dashboard/resumen?fecha=2026-08-27", headers=auth_headers)
    assert response.status_code == 200
    nombres = [c["nombre"] for c in response.json()["cuentas"]]
    assert "Caja" in nombres


def test_resumen_suma_ventas_y_comisiones_del_dia(client, db_session, auth_headers):
    servicio_id = _crear_servicio(db_session, "2.00")
    proveedor_id = _crear_proveedor(db_session)

    client.post(
        "/api/ventas",
        json={"items": [{"servicio_id": servicio_id, "cantidad": 5}]},
        headers=auth_headers,
    )
    client.post(
        "/api/comisiones/transacciones",
        json={"proveedor_id": proveedor_id, "valor_recibir": "100.00"},
        headers=auth_headers,
    )

    hoy = date.today().isoformat()
    response = client.get(f"/api/dashboard/resumen?fecha={hoy}", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["ventas"] == {"cantidad": 1, "total": "10.00"}
    assert body["comisiones"]["cantidad"] == 1
    assert body["comisiones"]["total_comision"] == "3.65"
    assert body["comisiones"]["total_valor_cobrado"] == "104.20"


def test_resumen_incluye_arqueo_del_dia(client, auth_headers):
    client.post("/api/arqueo/abrir", json={}, headers=auth_headers)

    hoy = date.today().isoformat()
    response = client.get(f"/api/dashboard/resumen?fecha={hoy}", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()["arqueos"]) == 1
    assert response.json()["arqueos"][0]["estado"] == "abierto"


def test_rango_agrega_ventas_de_varios_dias(client, db_session, auth_headers):
    servicio_id = _crear_servicio(db_session, "1.00")
    client.post(
        "/api/ventas",
        json={"items": [{"servicio_id": servicio_id, "cantidad": 3}]},
        headers=auth_headers,
    )

    hoy = date.today().isoformat()
    response = client.get(f"/api/dashboard/rango?desde={hoy}&hasta={hoy}", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["ventas"] == {"cantidad": 1, "total": "3.00"}


def test_rango_hasta_antes_de_desde_falla(client, auth_headers):
    response = client.get(
        "/api/dashboard/rango?desde=2026-08-27&hasta=2026-08-01", headers=auth_headers
    )
    assert response.status_code == 400


def test_dashboard_requiere_fecha(client, auth_headers):
    response = client.get("/api/dashboard/resumen", headers=auth_headers)
    assert response.status_code == 422


def test_dashboard_requiere_auth(client):
    response = client.get("/api/dashboard/resumen?fecha=2026-08-27")
    assert response.status_code == 401
