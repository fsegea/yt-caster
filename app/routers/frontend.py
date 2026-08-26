from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from app.config import Config
from app.deps import get_config

router = APIRouter()


@router.get("/")
async def index(config: Config = Depends(get_config)):
    return FileResponse(f"{config.static_dir}/index.html")