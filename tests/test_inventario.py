def test_crear_accesorio(client, auth_headers):
    response = client.post(
        "/api/inventario",
        json={"nombre": "Cable USB-C", "costo": "3.00", "precio_venta": "6.00"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["stock_actual"] == 0


def test_crear_accesorio_con_stock_inicial(client, auth_headers):
    response = client.post(
        "/api/inventario",
        json={"nombre": "Cable USB-C", "costo": "3.00", "precio_venta": "6.00", "stock_actual": 10},
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["stock_actual"] == 10


def test_listar_inventario(client, auth_headers):
    client.post(
        "/api/inventario",
        json={"nombre": "Cable USB-C", "costo": "3.00", "precio_venta": "6.00"},
        headers=auth_headers,
    )
    response = client.get("/api/inventario", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_patch_actualiza_precio_no_stock(client, auth_headers):
    creado = client.post(
        "/api/inventario",
        json={"nombre": "Cable USB-C", "costo": "3.00", "precio_venta": "6.00", "stock_actual": 5},
        headers=auth_headers,
    ).json()

    response = client.patch(
        f"/api/inventario/{creado['id']}",
        json={"precio_venta": "7.50"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["precio_venta"] == "7.50"
    assert body["stock_actual"] == 5


def test_movimiento_entrada_aumenta_stock(client, auth_headers):
    creado = client.post(
        "/api/inventario",
        json={"nombre": "Cable USB-C", "costo": "3.00", "precio_venta": "6.00"},
        headers=auth_headers,
    ).json()

    response = client.post(
        f"/api/inventario/{creado['id']}/movimiento",
        json={"tipo": "entrada", "cantidad": 20, "motivo": "compra"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["tipo"] == "entrada"

    accesorio = client.get("/api/inventario", headers=auth_headers).json()[0]
    assert accesorio["stock_actual"] == 20


def test_movimiento_salida_disminuye_stock(client, auth_headers):
    creado = client.post(
        "/api/inventario",
        json={"nombre": "Cable USB-C", "costo": "3.00", "precio_venta": "6.00", "stock_actual": 20},
        headers=auth_headers,
    ).json()

    response = client.post(
        f"/api/inventario/{creado['id']}/movimiento",
        json={"tipo": "salida", "cantidad": 5, "motivo": "venta"},
        headers=auth_headers,
    )
    assert response.status_code == 201

    accesorio = client.get("/api/inventario", headers=auth_headers).json()[0]
    assert accesorio["stock_actual"] == 15


def test_movimiento_salida_rechaza_stock_insuficiente(client, auth_headers):
    creado = client.post(
        "/api/inventario",
        json={"nombre": "Cable USB-C", "costo": "3.00", "precio_venta": "6.00", "stock_actual": 3},
        headers=auth_headers,
    ).json()

    response = client.post(
        f"/api/inventario/{creado['id']}/movimiento",
        json={"tipo": "salida", "cantidad": 10},
        headers=auth_headers,
    )
    assert response.status_code == 400

    accesorio = client.get("/api/inventario", headers=auth_headers).json()[0]
    assert accesorio["stock_actual"] == 3


def test_movimiento_tipo_invalido_falla(client, auth_headers):
    creado = client.post(
        "/api/inventario",
        json={"nombre": "Cable USB-C", "costo": "3.00", "precio_venta": "6.00"},
        headers=auth_headers,
    ).json()

    response = client.post(
        f"/api/inventario/{creado['id']}/movimiento",
        json={"tipo": "robo", "cantidad": 1},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_accesorio_inexistente_da_404(client, auth_headers):
    response = client.patch("/api/inventario/999", json={"nombre": "x"}, headers=auth_headers)
    assert response.status_code == 404


def test_inventario_requiere_auth(client):
    response = client.get("/api/inventario")
    assert response.status_code == 401
