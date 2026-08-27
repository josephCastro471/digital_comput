def test_crear_servicio_fijo(client, auth_headers):
    response = client.post(
        "/api/servicios",
        json={
            "nombre": "Impresion B/N",
            "categoria": "impresiones",
            "tipo_precio": "fijo",
            "precio_base": "0.10",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["precio_base"] == "0.10"
    assert body["escalones"] == []


def test_crear_servicio_fijo_sin_precio_base_falla(client, auth_headers):
    response = client.post(
        "/api/servicios",
        json={"nombre": "Impresion color", "categoria": "impresiones", "tipo_precio": "fijo"},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_crear_servicio_variable_sin_precio_base(client, auth_headers):
    response = client.post(
        "/api/servicios",
        json={"nombre": "Reparacion", "categoria": "servicios_tecnicos", "tipo_precio": "variable"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["precio_base"] is None


def test_crear_servicio_escalonado(client, auth_headers):
    response = client.post(
        "/api/servicios",
        json={
            "nombre": "Copias",
            "categoria": "impresiones",
            "tipo_precio": "escalonado",
            "escalones": [
                {"cantidad_desde": 1, "cantidad_hasta": 10, "precio_unitario": "0.10"},
                {"cantidad_desde": 11, "cantidad_hasta": None, "precio_unitario": "0.08"},
            ],
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert len(body["escalones"]) == 2
    assert body["escalones"][0]["precio_unitario"] == "0.10"


def test_crear_servicio_escalonado_sin_escalones_falla(client, auth_headers):
    response = client.post(
        "/api/servicios",
        json={"nombre": "Copias", "categoria": "impresiones", "tipo_precio": "escalonado"},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_crear_servicio_escalonado_con_precio_base_falla(client, auth_headers):
    response = client.post(
        "/api/servicios",
        json={
            "nombre": "Copias",
            "categoria": "impresiones",
            "tipo_precio": "escalonado",
            "precio_base": "0.10",
            "escalones": [{"cantidad_desde": 1, "cantidad_hasta": None, "precio_unitario": "0.10"}],
        },
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_crear_servicio_escalones_solapados_falla(client, auth_headers):
    response = client.post(
        "/api/servicios",
        json={
            "nombre": "Copias",
            "categoria": "impresiones",
            "tipo_precio": "escalonado",
            "escalones": [
                {"cantidad_desde": 1, "cantidad_hasta": 10, "precio_unitario": "0.10"},
                {"cantidad_desde": 5, "cantidad_hasta": None, "precio_unitario": "0.08"},
            ],
        },
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_listar_servicios(client, auth_headers):
    client.post(
        "/api/servicios",
        json={"nombre": "A", "categoria": "cat", "tipo_precio": "fijo", "precio_base": "1.00"},
        headers=auth_headers,
    )
    response = client.get("/api/servicios", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_patch_servicio_actualiza_precio_base(client, auth_headers):
    creado = client.post(
        "/api/servicios",
        json={"nombre": "A", "categoria": "cat", "tipo_precio": "fijo", "precio_base": "1.00"},
        headers=auth_headers,
    ).json()

    response = client.patch(
        f"/api/servicios/{creado['id']}",
        json={"precio_base": "1.50", "activo": False},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["precio_base"] == "1.50"
    assert body["activo"] is False


def test_patch_precio_base_en_escalonado_falla(client, auth_headers):
    creado = client.post(
        "/api/servicios",
        json={
            "nombre": "Copias",
            "categoria": "impresiones",
            "tipo_precio": "escalonado",
            "escalones": [{"cantidad_desde": 1, "cantidad_hasta": None, "precio_unitario": "0.10"}],
        },
        headers=auth_headers,
    ).json()

    response = client.patch(
        f"/api/servicios/{creado['id']}",
        json={"precio_base": "1.00"},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_delete_servicio(client, auth_headers):
    creado = client.post(
        "/api/servicios",
        json={"nombre": "A", "categoria": "cat", "tipo_precio": "fijo", "precio_base": "1.00"},
        headers=auth_headers,
    ).json()

    response = client.delete(f"/api/servicios/{creado['id']}", headers=auth_headers)
    assert response.status_code == 204

    response = client.get("/api/servicios", headers=auth_headers)
    assert response.json() == []

    response = client.delete(f"/api/servicios/{creado['id']}", headers=auth_headers)
    assert response.status_code == 404


def test_servicios_requiere_auth(client):
    response = client.get("/api/servicios")
    assert response.status_code == 401
