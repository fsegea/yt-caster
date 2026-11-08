import os
import re
import unicodedata
from dataclasses import dataclass

from app.config import Config
from app.services.historico import HistoricoService, es_id_valido

CARACTERES_NO_PERMITIDOS_RE = re.compile(r"[^A-Za-z0-9._-]+")
LONGITUD_MAXIMA_NOMBRE = 80


@dataclass(frozen=True)
class ArchivoDescargable:
    """Un vídeo ya descargado en el servidor, listo para enviarse al cliente."""

    ruta: str
    nombre: str
    tamano: int


class ArchivoService:
    """Resuelve los vídeos almacenados en el servidor para descargarlos en el cliente."""

    def __init__(self, config: Config, historico: HistoricoService):
        self.config = config
        self.historico = historico

    def video_actual(self, titulo: str = "") -> ArchivoDescargable | None:
        """El vídeo de la última descarga (video.mp4), si existe."""
        return self._resolver(self.config.ruta_video, titulo or "video")

    def video_historico(self, entry_id: str) -> ArchivoDescargable | None:
        """Un vídeo guardado en el histórico, si existe."""
        if not es_id_valido(entry_id):
            return None

        ruta = self.historico.ruta_video_guardado(entry_id)
        if ruta is None:
            return None

        entrada = self.historico.obtener(entry_id) or {}
        return self._resolver(ruta, entrada.get("titulo", "") or entry_id)

    def _resolver(self, ruta: str, titulo: str) -> ArchivoDescargable | None:
        try:
            stat = os.stat(ruta)
        except OSError:
            return None

        if not os.path.isfile(ruta):
            return None

        return ArchivoDescargable(
            ruta=ruta,
            nombre=self.nombre_archivo(titulo),
            tamano=stat.st_size,
        )

    @staticmethod
    def nombre_archivo(titulo: str) -> str:
        """Convierte un título en un nombre de fichero seguro para la descarga."""
        normalizado = unicodedata.normalize("NFKD", titulo or "")
        sin_acentos = "".join(c for c in normalizado if not unicodedata.combining(c))
        limpio = CARACTERES_NO_PERMITIDOS_RE.sub("_", sin_acentos).strip("._-")
        limpio = limpio[:LONGITUD_MAXIMA_NOMBRE].rstrip("._-")
        if not limpio:
            limpio = "video"
        return f"{limpio}.mp4"
