from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import Config
from app.state import EstadoApp
from app.services.chromecast import ChromecastService
from app.services.download import DescargaService
from app.services.historico import HistoricoService
from app.routers import frontend, download, controls, chromecast, health, historico


def create_app(
    config: Config | None = None,
    estado: EstadoApp | None = None,
    descarga_service: DescargaService | None = None,
    chromecast_service: ChromecastService | None = None,
    historico_service: HistoricoService | None = None,
) -> FastAPI:
    config = config or Config()
    estado = estado or EstadoApp(ip_chromecast=config.chromecast_ip)
    descarga_service = descarga_service or DescargaService(config, estado)
    chromecast_service = chromecast_service or ChromecastService(config, estado)
    historico_service = historico_service or HistoricoService(config)

    app = FastAPI()
    app.state.config = config
    app.state.estado = estado
    app.state.descarga_service = descarga_service
    app.state.chromecast_service = chromecast_service
    app.state.historico_service = historico_service

    app.mount("/static", StaticFiles(directory=config.static_dir), name="static")

    app.include_router(frontend.router)
    app.include_router(download.router)
    app.include_router(controls.router)
    app.include_router(chromecast.router)
    app.include_router(health.router)
    app.include_router(historico.router)
    return app


app = create_app()