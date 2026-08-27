def test_crear_entrada_empresa(client, auth_headers):
    response = client.post(
        "/api/directorio",
        json={
            "tipo": "empresa",
            "nombre": "CNT",
            "codigo": "001",
            "red": "Pichincha",
            "nota": "pagos de internet",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["nombre"] == "CNT"
    assert body["codigo"] == "001"


def test_crear_entrada_cliente_minima(client, auth_headers):
    response = client.post(
        "/api/directorio",
        json={"tipo": "cliente", "nombre": "Juan Perez"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["codigo"] is None


def test_listar_directorio(client, auth_headers):
    client.post("/api/directorio", json={"tipo": "empresa", "nombre": "CNT"}, headers=auth_headers)
    client.post("/api/directorio", json={"tipo": "cliente", "nombre": "Juan Perez"}, headers=auth_headers)

    response = client.get("/api/directorio", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_buscar_filtra_por_nombre(client, auth_headers):
    client.post("/api/directorio", json={"tipo": "empresa", "nombre": "CNT"}, headers=auth_headers)
    client.post("/api/directorio", json={"tipo": "cliente", "nombre": "Juan Perez"}, headers=auth_headers)

    response = client.get("/api/directorio?buscar=juan", headers=auth_headers)
    assert response.status_code == 200
    nombres = [d["nombre"] for d in response.json()]
    assert nombres == ["Juan Perez"]


def test_buscar_filtra_por_codigo(client, auth_headers):
    client.post(
        "/api/directorio",
        json={"tipo": "empresa", "nombre": "CNT", "codigo": "XJ99"},
        headers=auth_headers,
    )
    client.post("/api/directorio", json={"tipo": "cliente", "nombre": "Juan Perez"}, headers=auth_headers)

    response = client.get("/api/directorio?buscar=xj99", headers=auth_headers)
    assert len(response.json()) == 1
    assert response.json()[0]["nombre"] == "CNT"


def test_patch_actualiza_y_permite_limpiar_campo(client, auth_headers):
    creado = client.post(
        "/api/directorio",
        json={"tipo": "empresa", "nombre": "CNT", "codigo": "001"},
        headers=auth_headers,
    ).json()

    response = client.patch(
        f"/api/directorio/{creado['id']}",
        json={"codigo": None, "nota": "actualizado"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["codigo"] is None
    assert body["nota"] == "actualizado"
    assert body["nombre"] == "CNT"


def test_delete_directorio(client, auth_headers):
    creado = client.post(
        "/api/directorio", json={"tipo": "cliente", "nombre": "Juan Perez"}, headers=auth_headers
    ).json()

    response = client.delete(f"/api/directorio/{creado['id']}", headers=auth_headers)
    assert response.status_code == 204

    response = client.get("/api/directorio", headers=auth_headers)
    assert response.json() == []


def test_directorio_inexistente_da_404(client, auth_headers):
    response = client.patch(
        "/api/directorio/999", json={"nombre": "x"}, headers=auth_headers
    )
    assert response.status_code == 404


def test_directorio_requiere_auth(client):
    response = client.get("/api/directorio")
    assert response.status_code == 401
