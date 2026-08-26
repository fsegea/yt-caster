from fastapi.testclient import TestClient

from app.config import Config
from app.main import create_app


def test_salud(client):
    r = client.get("/salud")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_version(client):
    r = client.get("/version")
    assert r.status_code == 200
    assert r.json()["version"] == "v9.9.9"
    assert r.json()["yt_dlp_version"]


def test_version_sin_archivo(config, fakes):
    config_sin = Config(
        descargas_dir=config.descargas_dir,
        chromecast_ip=config.chromecast_ip,
        ruta_version=str(config.descargas_dir) + "/inexistente",
    )
    app = create_app(
        config=config_sin,
        descarga_service=fakes["descarga"],
        chromecast_service=fakes["chromecast"],
    )
    r = TestClient(app).get("/version")
    assert r.status_code == 200
    assert r.json()["version"] == "unknown"
    assert r.json()["yt_dlp_version"]


def test_index(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Chromecast" in r.text


def test_static(client):
    r = client.get("/static/index.html")
    assert r.status_code == 200
    assert "Chromecast" in r.text