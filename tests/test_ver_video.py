CONTENIDO = b"0123456789abcdef"


def _simular_descarga(app, titulo="Mi vídeo", contenido=CONTENIDO):
    with open(app.state.config.ruta_video, "wb") as f:
        f.write(contenido)
    app.state.estado.actualizar(
        "job1", "https://example.com/v", "correcto", "Descarga completada", titulo=titulo
    )


def _guardar_en_historico(client, app, titulo="Vídeo guardado"):
    _simular_descarga(app, titulo=titulo)
    return client.post("/historico").json()


# --- Vídeo actual ---

def test_ver_video_sin_descarga(client):
    r = client.get("/video/ver")
    assert r.status_code == 404


def test_ver_video_se_reproduce_en_el_navegador(client, app):
    _simular_descarga(app)

    r = client.get("/video/ver")

    assert r.status_code == 200
    assert r.content == CONTENIDO
    assert r.headers["content-type"] == "video/mp4"
    assert 'inline' in r.headers["content-disposition"]
    assert "attachment" not in r.headers["content-disposition"]
    assert "Mi_video.mp4" in r.headers["content-disposition"]


def test_descargar_y_ver_no_se_confunden(client, app):
    """`/video` sigue descargando el fichero; `/video/ver` lo reproduce en línea."""
    _simular_descarga(app)

    descarga = client.get("/video")
    visionado = client.get("/video/ver")

    assert "attachment" in descarga.headers["content-disposition"]
    assert "attachment" not in visionado.headers["content-disposition"]


def test_ver_video_anuncia_soporte_de_range(client, app):
    _simular_descarga(app)

    r = client.get("/video/ver")

    assert r.headers["accept-ranges"] == "bytes"
    assert r.headers["content-length"] == str(len(CONTENIDO))


def test_ver_video_admite_range_para_buscar_dentro_del_video(client, app):
    """El seek del <video> va por Range: hay que devolver solo ese trozo (206)."""
    _simular_descarga(app)

    r = client.get("/video/ver", headers={"range": "bytes=4-7"})

    assert r.status_code == 206
    assert r.content == b"4567"
    assert r.headers["content-range"] == f"bytes 4-7/{len(CONTENIDO)}"


def test_ver_video_admite_range_sin_fin(client, app):
    _simular_descarga(app)

    r = client.get("/video/ver", headers={"range": "bytes=10-"})

    assert r.status_code == 206
    assert r.content == CONTENIDO[10:]


def test_ver_video_admite_range_de_sufijo(client, app):
    _simular_descarga(app)

    r = client.get("/video/ver", headers={"range": "bytes=-4"})

    assert r.status_code == 206
    assert r.content == CONTENIDO[-4:]


def test_ver_video_range_fuera_de_rango(client, app):
    _simular_descarga(app)

    r = client.get("/video/ver", headers={"range": "bytes=999999-1000000"})

    assert r.status_code == 416
    assert r.headers["content-range"] == f"bytes */{len(CONTENIDO)}"


def test_ver_video_sin_range_devuelve_el_fichero_completo(client, app):
    _simular_descarga(app)

    r = client.get("/video/ver")

    assert r.status_code == 200
    assert r.content == CONTENIDO


# --- Vídeos del histórico ---

def test_ver_historico(client, app):
    entrada = _guardar_en_historico(client, app)

    r = client.get(f"/historico/{entrada['id']}/ver")

    assert r.status_code == 200
    assert r.content == CONTENIDO
    assert r.headers["content-type"] == "video/mp4"
    assert 'inline' in r.headers["content-disposition"]
    assert "Video_guardado.mp4" in r.headers["content-disposition"]


def test_ver_historico_admite_range(client, app):
    entrada = _guardar_en_historico(client, app)

    r = client.get(f"/historico/{entrada['id']}/ver", headers={"range": "bytes=0-3"})

    assert r.status_code == 206
    assert r.content == CONTENIDO[:4]


def test_ver_historico_no_guardado(client):
    r = client.get("/historico/no-existe/ver")
    assert r.status_code == 404


def test_ver_historico_id_malformado(client):
    for entry_id in ["%2e%2e", "%2e%2e%2fetc%2fpasswd", "a" * 65, "no-existe"]:
        r = client.get(f"/historico/{entry_id}/ver")
        assert r.status_code == 404, entry_id


def test_ver_historico_tras_eliminar(client, app):
    entrada = _guardar_en_historico(client, app)
    client.delete(f"/historico/{entrada['id']}")

    r = client.get(f"/historico/{entrada['id']}/ver")
    assert r.status_code == 404
