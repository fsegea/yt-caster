def test_chromecast_get(client):
    r = client.get("/chromecast")
    assert r.status_code == 200
    assert r.json() == {"ip": "10.0.0.1"}


def test_chromecast_set(client):
    r = client.post("/chromecast", json={"ip": "192.168.1.50"})
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "ip": "192.168.1.50"}
    r2 = client.get("/chromecast")
    assert r2.json() == {"ip": "192.168.1.50"}


def test_chromecast_set_invalido(client):
    r = client.post("/chromecast", json={})
    assert r.status_code == 422


def test_descargar_y_estado(client, app):
    r = client.post("/descargar", json={"url": "https://example.com/v"})
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "descargando"
    job_id = data["job_id"]
    assert job_id

    assert app.state.descarga_service.calls == [("https://example.com/v", job_id)]

    r2 = client.get("/estado")
    job = r2.json()["job"]
    assert job["id"] == job_id
    assert job["estado"] == "descargando"
    assert job["mensaje"] == "Descargando video..."
    assert job["url"] == "https://example.com/v"


def test_descargar_sin_url(client):
    r = client.post("/descargar", json={})
    assert r.status_code == 422


def test_estado_sin_jobs(client):
    r = client.get("/estado")
    assert r.json() == {"job": None}