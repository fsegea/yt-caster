import threading
import time
from typing import Any


class EstadoApp:
    def __init__(self, ip_chromecast: str):
        self._lock = threading.RLock()
        self._ip_chromecast = ip_chromecast
        self._estado_actual: dict[str, Any] | None = None
        self._id_job_activo: str | None = None
        self._proceso_actual: Any = None

    def get_chromecast_ip(self) -> str:
        with self._lock:
            return self._ip_chromecast

    def set_chromecast_ip(self, ip: str) -> None:
        with self._lock:
            self._ip_chromecast = ip

    def get_estado(self) -> dict[str, Any] | None:
        with self._lock:
            return dict(self._estado_actual) if self._estado_actual else None

    def es_job_activo(self, job_id: str) -> bool:
        with self._lock:
            return self._id_job_activo == job_id

    def actualizar(
        self, job_id: str, url: str, estado: str, mensaje: str = "", titulo: str = ""
    ) -> None:
        with self._lock:
            titulo_previo = (
                self._estado_actual.get("titulo", "")
                if self._estado_actual and self._estado_actual.get("id") == job_id
                else ""
            )
            self._id_job_activo = job_id
            ahora = time.time()
            self._estado_actual = {
                "id": job_id,
                "url": url,
                "estado": estado,
                "mensaje": mensaje,
                "titulo": titulo or titulo_previo,
                "iniciado_at": ahora,
                "actualizado_at": ahora,
            }

    def get_proceso(self) -> Any:
        with self._lock:
            return self._proceso_actual

    def set_proceso(self, proceso: Any) -> None:
        with self._lock:
            self._proceso_actual = proceso

    def limpiar_proceso(self, proceso: Any) -> None:
        with self._lock:
            if self._proceso_actual is proceso:
                self._proceso_actual = None
