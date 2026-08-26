from fastapi import APIRouter, Depends
from yt_dlp.version import __version__ as YT_DLP_VERSION

from app.config import Config
from app.deps import get_config

router = APIRouter()


@router.get("/salud")
async def salud():
    return {"status": "ok"}


@router.get("/version")
async def version(config: Config = Depends(get_config)):
    try:
        with open(config.ruta_version) as f:
            v = f.read().strip()
    except FileNotFoundError:
        v = "unknown"
    return {"version": v, "yt_dlp_version": YT_DLP_VERSION}