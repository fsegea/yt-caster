from fastapi import Request

from app.config import Config
from app.state import EstadoApp
from app.services.chromecast import ChromecastService
from app.services.download import DescargaService


def get_config(request: Request) -> Config:
    return request.app.state.config


def get_estado(request: Request) -> EstadoApp:
    return request.app.state.estado


def get_descarga_service(request: Request) -> DescargaService:
    return request.app.state.descarga_service


def get_chromecast_service(request: Request) -> ChromecastService:
    return request.app.state.chromecast_service