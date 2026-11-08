def _descargar_completa(app, url="https://example.com/v", titulo="Mi vídeo", contenido=b"datos"):
    with open(app.state.config.ruta_video, "wb") as f:
        f.write(contenido)
    app.state.estado.actualizar("job1", url, "correcto", "Descarga completada", titulo=titulo)


# --- Vídeo actual ---

def test_descargar_video_sin_descarga_previa(client):
    r = client.get("/video")
    assert r.status_code == 404


def test_descargar_video_devuelve_el_fichero(client, app):
    _descargar_completa(app)

    r = client.get("/video")

    assert r.status_code == 200
    assert r.content == b"datos"
    assert r.headers["content-type"] == "video/mp4"
    assert 'attachment' in r.headers["content-disposition"]
    assert "Mi_video.mp4" in r.headers["content-disposition"]


def test_descargar_video_usa_titulo_del_job(client, app):
    _descargar_completa(app, titulo="Otro/título: raro")

    r = client.get("/video")

    assert "Otro_titulo_raro.mp4" in r.headers["content-disposition"]


def test_descargar_video_sin_titulo_en_estado(client, app):
    with open(app.state.config.ruta_video, "wb") as f:
        f.write(b"datos")

    r = client.get("/video")

    assert r.status_code == 200
    assert "video.mp4" in r.headers["content-disposition"]


def test_descargar_video_admite_range(client, app):
    _descargar_completa(app, contenido=b"0123456789")

    r = client.get("/video", headers={"range": "bytes=2-5"})

    assert r.status_code == 206
    assert r.content == b"2345"


def test_info_video_sin_descarga(client):
    r = client.get("/video/info")
    assert r.status_code == 200
    assert r.json() == {"disponible": False}


def test_info_video_con_descarga(client, app):
    _descargar_completa(app)

    r = client.get("/video/info")

    assert r.status_code == 200
    data = r.json()
    assert data["disponible"] is True
    assert data["nombre"] == "Mi_video.mp4"
    assert data["tamano"] == 5


# --- Vídeos del histórico ---

def _guardar_en_historico(client, app, titulo="Vídeo guardado"):
    _descargar_completa(app, titulo=titulo)
    return client.post("/historico").json()


def test_descargar_historico(client, app):
    entrada = _guardar_en_historico(client, app)

    r = client.get(f"/historico/{entrada['id']}/descargar")

    assert r.status_code == 200
    assert r.content == b"datos"
    assert r.headers["content-type"] == "video/mp4"
    assert "Video_guardado.mp4" in r.headers["content-disposition"]


def test_descargar_historico_no_guardado(client):
    r = client.get("/historico/no-existe/descargar")
    assert r.status_code == 404


def test_descargar_historico_id_malformado(client):
    for entry_id in ["%2e%2e", "%2e%2e%2fetc%2fpasswd", "a" * 65, "no-existe"]:
        r = client.get(f"/historico/{entry_id}/descargar")
        assert r.status_code == 404, entry_id


def test_descargar_historico_tras_eliminar(client, app):
    entrada = _guardar_en_historico(client, app)
    client.delete(f"/historico/{entrada['id']}")

    r = client.get(f"/historico/{entrada['id']}/descargar")
    assert r.status_code == 404


def test_historico_listado_incluye_tamano(client, app):
    _guardar_en_historico(client, app)

    videos = client.get("/historico").json()["videos"]

    assert videos[0]["tamano"] == 5
