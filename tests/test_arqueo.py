def test_abrir_arqueo_default_40(client, auth_headers):
    response = client.post("/api/arqueo/abrir", json={}, headers=auth_headers)
    assert response.status_code == 201
    body = response.json()
    assert body["saldo_apertura"] == "40.00"
    assert body["estado"] == "abierto"
    assert body["fecha_cierre"] is None


def test_no_permite_dos_turnos_abiertos(client, auth_headers):
    client.post("/api/arqueo/abrir", json={}, headers=auth_headers)
    response = client.post("/api/arqueo/abrir", json={}, headers=auth_headers)
    assert response.status_code == 409


def test_cerrar_arqueo_calcula_ganancia_neta(client, auth_headers):
    abierto = client.post(
        "/api/arqueo/abrir", json={"saldo_apertura": "40.00"}, headers=auth_headers
    ).json()

    response = client.post(
        f"/api/arqueo/{abierto['id']}/cerrar",
        json={
            "detalles": [
                {"denominacion": "20.00", "cantidad": 3},
                {"denominacion": "1.00", "cantidad": 5},
            ]
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["estado"] == "cerrado"
    assert body["saldo_cierre"] == "65.00"
    assert body["ganancia_neta"] == "25.00"
    assert body["fecha_cierre"] is not None
    assert len(body["detalles"]) == 2


def test_cerrar_libera_para_abrir_otro_turno(client, auth_headers):
    abierto = client.post("/api/arqueo/abrir", json={}, headers=auth_headers).json()
    client.post(
        f"/api/arqueo/{abierto['id']}/cerrar",
        json={"detalles": [{"denominacion": "1.00", "cantidad": 40}]},
        headers=auth_headers,
    )

    response = client.post("/api/arqueo/abrir", json={}, headers=auth_headers)
    assert response.status_code == 201


def test_cerrar_arqueo_ya_cerrado_falla(client, auth_headers):
    abierto = client.post("/api/arqueo/abrir", json={}, headers=auth_headers).json()
    client.post(
        f"/api/arqueo/{abierto['id']}/cerrar",
        json={"detalles": [{"denominacion": "1.00", "cantidad": 40}]},
        headers=auth_headers,
    )

    response = client.post(
        f"/api/arqueo/{abierto['id']}/cerrar",
        json={"detalles": [{"denominacion": "1.00", "cantidad": 40}]},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_cerrar_sin_detalles_falla(client, auth_headers):
    abierto = client.post("/api/arqueo/abrir", json={}, headers=auth_headers).json()

    response = client.post(
        f"/api/arqueo/{abierto['id']}/cerrar",
        json={"detalles": []},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_listar_arqueos_filtra_por_estado(client, auth_headers):
    abierto = client.post("/api/arqueo/abrir", json={}, headers=auth_headers).json()

    response = client.get("/api/arqueo?estado=abierto", headers=auth_headers)
    assert response.status_code == 200
    ids = [a["id"] for a in response.json()]
    assert abierto["id"] in ids

    response = client.get("/api/arqueo?estado=cerrado", headers=auth_headers)
    assert abierto["id"] not in [a["id"] for a in response.json()]


def test_arqueo_inexistente_da_404(client, auth_headers):
    response = client.get("/api/arqueo/999", headers=auth_headers)
    assert response.status_code == 404


def test_arqueo_requiere_auth(client):
    response = client.get("/api/arqueo")
    assert response.status_code == 401
