import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse

from app.deps import get_archivo_service, get_descarga_service, get_estado
from app.models import SolicitudVideo
from app.services.archivo import ArchivoService
from app.services.download import DescargaService
from app.state import EstadoApp

router = APIRouter()


@router.post("/descargar")
async def recibir_video(
    req: SolicitudVideo,
    background_tasks: BackgroundTasks,
    descarga_service: DescargaService = Depends(get_descarga_service),
    estado: EstadoApp = Depends(get_estado),
):
    job_id = uuid.uuid4().hex
    estado.actualizar(job_id, req.url, "descargando", "Descargando video...")
    background_tasks.add_task(descarga_service.descargar, req.url, job_id)
    return {"status": "descargando", "job_id": job_id, "url": req.url}


@router.get("/estado")
async def obtener_estado(estado: EstadoApp = Depends(get_estado)):
    return {"job": estado.get_estado()}


@router.get("/video")
async def descargar_video(
    estado: EstadoApp = Depends(get_estado),
    archivo_service: ArchivoService = Depends(get_archivo_service),
):
    """Envía al cliente el vídeo descargado actualmente en el servidor."""
    job = estado.get_estado() or {}
    archivo = archivo_service.video_actual(job.get("titulo", ""))
    if archivo is None:
        raise HTTPException(
            status_code=404,
            detail="No hay ningún vídeo descargado en el servidor",
        )

    return FileResponse(
        archivo.ruta,
        media_type="video/mp4",
        filename=archivo.nombre,
    )


@router.get("/video/info")
async def info_video(
    estado: EstadoApp = Depends(get_estado),
    archivo_service: ArchivoService = Depends(get_archivo_service),
):
    """Indica si hay un vídeo descargado disponible para descargar en el cliente."""
    job = estado.get_estado() or {}
    archivo = archivo_service.video_actual(job.get("titulo", ""))
    if archivo is None:
        return {"disponible": False}

    return {
        "disponible": True,
        "nombre": archivo.nombre,
        "tamano": archivo.tamano,
    }