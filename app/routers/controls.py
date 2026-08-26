from fastapi import APIRouter, BackgroundTasks, Depends

from app.config import Config
from app.deps import get_chromecast_service, get_config
from app.models import DeltaTiempo, DeltaVolumen, SolicitudSeek
from app.services.chromecast import ChromecastService

router = APIRouter()


def _en_cola(
    background_tasks: BackgroundTasks,
    chromecast_service: ChromecastService,
    comando: str,
    *args: str,
) -> None:
    background_tasks.add_task(chromecast_service.ejecutar, comando, *args)


@router.post("/play")
async def play(
    background_tasks: BackgroundTasks,
    config: Config = Depends(get_config),
    chromecast_service: ChromecastService = Depends(get_chromecast_service),
):
    _en_cola(background_tasks, chromecast_service, "cast", config.ruta_video)
    return {"status": "ok"}


@router.post("/stop")
async def stop(
    background_tasks: BackgroundTasks,
    chromecast_service: ChromecastService = Depends(get_chromecast_service),
):
    _en_cola(background_tasks, chromecast_service, "stop")
    return {"status": "ok"}


@router.post("/pause")
async def pause(
    background_tasks: BackgroundTasks,
    chromecast_service: ChromecastService = Depends(get_chromecast_service),
):
    _en_cola(background_tasks, chromecast_service, "pause")
    return {"status": "ok"}


@router.post("/play-toggle")
async def play_toggle(
    background_tasks: BackgroundTasks,
    chromecast_service: ChromecastService = Depends(get_chromecast_service),
):
    _en_cola(background_tasks, chromecast_service, "play_toggle")
    return {"status": "ok"}


@router.post("/volumeup")
async def volumeup(
    background_tasks: BackgroundTasks,
    chromecast_service: ChromecastService = Depends(get_chromecast_service),
    req: DeltaVolumen | None = None,
):
    delta = req.delta if req else 10
    _en_cola(background_tasks, chromecast_service, "volumeup", str(delta))
    return {"status": "ok", "delta": delta}


@router.post("/volumedown")
async def volumedown(
    background_tasks: BackgroundTasks,
    chromecast_service: ChromecastService = Depends(get_chromecast_service),
    req: DeltaVolumen | None = None,
):
    delta = req.delta if req else 10
    _en_cola(background_tasks, chromecast_service, "volumedown", str(delta))
    return {"status": "ok", "delta": delta}


@router.post("/ffwd")
async def ffwd(
    background_tasks: BackgroundTasks,
    chromecast_service: ChromecastService = Depends(get_chromecast_service),
    req: DeltaTiempo | None = None,
):
    time_val = req.time if req else 30
    _en_cola(background_tasks, chromecast_service, "ffwd", str(time_val))
    return {"status": "ok", "time": time_val}


@router.post("/rewind")
async def rewind(
    background_tasks: BackgroundTasks,
    chromecast_service: ChromecastService = Depends(get_chromecast_service),
    req: DeltaTiempo | None = None,
):
    time_val = req.time if req else 30
    _en_cola(background_tasks, chromecast_service, "rewind", str(time_val))
    return {"status": "ok", "time": time_val}


@router.post("/seek")
async def seek(
    req: SolicitudSeek,
    background_tasks: BackgroundTasks,
    chromecast_service: ChromecastService = Depends(get_chromecast_service),
):
    _en_cola(background_tasks, chromecast_service, "seek", req.time)
    return {"status": "ok", "time": req.time}