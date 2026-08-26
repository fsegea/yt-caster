import uuid

from fastapi import APIRouter, BackgroundTasks, Depends

from app.deps import get_descarga_service, get_estado
from app.models import SolicitudVideo
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