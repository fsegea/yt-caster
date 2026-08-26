import pytest
from fastapi.testclient import TestClient

from app.config import Config
from app.main import create_app


class FakeDescargaService:
    def __init__(self):
        self.calls: list[tuple[str, str]] = []

    async def descargar(self, url: str, job_id: str) -> None:
        self.calls.append((url, job_id))


class FakeChromecastService:
    def __init__(self):
        self.calls: list[tuple[str, tuple]] = []

    async def ejecutar(self, comando: str, *args: str) -> None:
        self.calls.append((comando, args))


@pytest.fixture
def config(tmp_path):
    (tmp_path / "VERSION").write_text("v9.9.9\n")
    return Config(
        descargas_dir=str(tmp_path),
        chromecast_ip="10.0.0.1",
        static_dir="static",
        ruta_version=str(tmp_path / "VERSION"),
    )


@pytest.fixture
def fakes():
    return {
        "descarga": FakeDescargaService(),
        "chromecast": FakeChromecastService(),
    }


@pytest.fixture
def app(config, fakes):
    return create_app(
        config=config,
        descarga_service=fakes["descarga"],
        chromecast_service=fakes["chromecast"],
    )


@pytest.fixture
def client(app):
    return TestClient(app)