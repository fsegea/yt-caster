def _descargar_completa(app, url="https://example.com/v", titulo="Mi vídeo"):
    with open(app.state.config.ruta_video, "wb") as f:
        f.write(b"datos")
    app.state.estado.actualizar("job1", url, "correcto", "Descarga completada", titulo=titulo)


def test_guardar_historico_sin_descarga_previa(client):
    r = client.post("/historico")
    assert r.status_code == 400


def test_guardar_historico_ok(client, app):
    _descargar_completa(app)

    r = client.post("/historico")
    assert r.status_code == 200
    data = r.json()
    assert data["titulo"] == "Mi vídeo"
    assert data["url"] == "https://example.com/v"
    assert "id" in data


def test_guardar_historico_con_descarga_en_curso_falla(client, app):
    app.state.estado.actualizar("job1", "http://u", "descargando", "Descargando video...")
    r = client.post("/historico")
    assert r.status_code == 400


def test_listar_historico(client, app):
    _descargar_completa(app)
    client.post("/historico")

    r = client.get("/historico")
    assert r.status_code == 200
    videos = r.json()["videos"]
    assert len(videos) == 1
    assert videos[0]["titulo"] == "Mi vídeo"


def test_eliminar_historico(client, app):
    _descargar_completa(app)
    entrada = client.post("/historico").json()

    r = client.delete(f"/historico/{entrada['id']}")
    assert r.status_code == 200
    assert client.get("/historico").json()["videos"] == []


def test_eliminar_historico_inexistente(client):
    r = client.delete("/historico/no-existe")
    assert r.status_code == 404


def test_reproducir_historico(client, app):
    _descargar_completa(app)
    entrada = client.post("/historico").json()

    r = client.post(f"/historico/{entrada['id']}/play")
    assert r.status_code == 200
    assert app.state.chromecast_service.calls
    comando, args = app.state.chromecast_service.calls[0]
    assert comando == "cast"
    assert args[0].endswith(f"{entrada['id']}.mp4")


def test_reproducir_historico_inexistente(client):
    r = client.post("/historico/no-existe/play")
    assert r.status_code == 404
