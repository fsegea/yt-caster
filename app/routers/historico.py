from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.config import Config
from app.deps import get_chromecast_service, get_config, get_estado, get_historico_service
from app.services.chromecast import ChromecastService
from app.services.historico import HistoricoService
from app.state import EstadoApp

router = APIRouter()


@router.post("/historico")
async def guardar_en_historico(
    config: Config = Depends(get_config),
    estado: EstadoApp = Depends(get_estado),
    historico_service: HistoricoService = Depends(get_historico_service),
):
    job = estado.get_estado()
    if not job or job.get("estado") != "correcto":
        raise HTTPException(
            status_code=400,
            detail="No hay ningún vídeo descargado correctamente para guardar",
        )

    try:
        entrada = historico_service.guardar(
            job["url"], job.get("titulo", ""), config.ruta_video
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return entrada


@router.get("/historico")
async def listar_historico(
    historico_service: HistoricoService = Depends(get_historico_service),
):
    return {"videos": historico_service.listar()}


@router.delete("/historico/{entry_id}")
async def eliminar_historico(
    entry_id: str,
    historico_service: HistoricoService = Depends(get_historico_service),
):
    if not historico_service.eliminar(entry_id):
        raise HTTPException(status_code=404, detail="Vídeo no encontrado en el histórico")
    return {"status": "ok"}


@router.post("/historico/{entry_id}/play")
async def reproducir_historico(
    entry_id: str,
    background_tasks: BackgroundTasks,
    historico_service: HistoricoService = Depends(get_historico_service),
    chromecast_service: ChromecastService = Depends(get_chromecast_service),
):
    ruta = historico_service.ruta_video_guardado(entry_id)
    if ruta is None:
        raise HTTPException(status_code=404, detail="Vídeo no encontrado en el histórico")

    background_tasks.add_task(chromecast_service.ejecutar, "cast", ruta)
    return {"status": "ok"}
