from fastapi import APIRouter, BackgroundTasks, Depends

from app.deps import get_config, get_estado, get_chromecast_service
from app.models import SolicitudIP
from app.services.chromecast import ChromecastService
from app.state import EstadoApp

router = APIRouter()


@router.get("/chromecast")
async def get_chromecast(estado: EstadoApp = Depends(get_estado)):
    return {"ip": estado.get_chromecast_ip()}


@router.post("/chromecast")
async def set_chromecast(
    req: SolicitudIP,
    estado: EstadoApp = Depends(get_estado),
):
    estado.set_chromecast_ip(req.ip)
    return {"status": "ok", "ip": req.ip}