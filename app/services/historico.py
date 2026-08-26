import json
import os
import shutil
import time
import uuid

from app.config import Config


class HistoricoService:
    """Gestiona copias persistentes de vídeos descargados (marcar/listar/eliminar)."""

    def __init__(self, config: Config):
        self.config = config

    def _asegurar_dir(self) -> None:
        os.makedirs(self.config.historico_dir, exist_ok=True)

    def _ruta_video(self, entry_id: str) -> str:
        return f"{self.config.historico_dir}/{entry_id}.mp4"

    def _ruta_meta(self, entry_id: str) -> str:
        return f"{self.config.historico_dir}/{entry_id}.json"

    def guardar(self, url: str, titulo: str, ruta_origen: str) -> dict:
        if not os.path.exists(ruta_origen):
            raise FileNotFoundError("No hay ningún vídeo descargado para guardar")

        self._asegurar_dir()
        entry_id = uuid.uuid4().hex
        shutil.copy2(ruta_origen, self._ruta_video(entry_id))

        entrada = {
            "id": entry_id,
            "titulo": titulo or url,
            "url": url,
            "fecha": time.time(),
        }
        with open(self._ruta_meta(entry_id), "w") as f:
            json.dump(entrada, f)
        return entrada

    def listar(self) -> list[dict]:
        self._asegurar_dir()
        entradas = []
        for nombre in os.listdir(self.config.historico_dir):
            if not nombre.endswith(".json"):
                continue
            try:
                with open(f"{self.config.historico_dir}/{nombre}") as f:
                    entradas.append(json.load(f))
            except (json.JSONDecodeError, OSError):
                continue
        entradas.sort(key=lambda e: e.get("fecha", 0), reverse=True)
        return entradas

    def obtener(self, entry_id: str) -> dict | None:
        ruta_meta = self._ruta_meta(entry_id)
        if not os.path.exists(ruta_meta):
            return None
        try:
            with open(ruta_meta) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

    def ruta_video_guardado(self, entry_id: str) -> str | None:
        ruta = self._ruta_video(entry_id)
        return ruta if os.path.exists(ruta) else None

    def eliminar(self, entry_id: str) -> bool:
        existia = False
        ruta_video = self._ruta_video(entry_id)
        ruta_meta = self._ruta_meta(entry_id)
        if os.path.exists(ruta_video):
            os.remove(ruta_video)
            existia = True
        if os.path.exists(ruta_meta):
            os.remove(ruta_meta)
            existia = True
        return existia
