import json
import os
import re
import shutil
import time
import uuid

from app.config import Config

ID_RE = re.compile(r"^[0-9a-fA-F]{1,64}$")


def es_id_valido(entry_id: str) -> bool:
    """Evita ids malformados (p. ej. con rutas relativas) al construir ficheros."""
    return isinstance(entry_id, str) and ID_RE.fullmatch(entry_id) is not None


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
        ruta_destino = self._ruta_video(entry_id)
        shutil.copy2(ruta_origen, ruta_destino)

        entrada = {
            "id": entry_id,
            "titulo": titulo or url,
            "url": url,
            "fecha": time.time(),
            "tamano": os.path.getsize(ruta_destino),
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
            entry_id = nombre[: -len(".json")]
            try:
                with open(f"{self.config.historico_dir}/{nombre}") as f:
                    entrada = json.load(f)
            except (json.JSONDecodeError, OSError):
                continue

            if not isinstance(entrada, dict):
                continue

            entrada.setdefault("id", entry_id)
            if "tamano" not in entrada:
                tamano = self._tamano(entry_id)
                if tamano is not None:
                    entrada["tamano"] = tamano

            entradas.append(entrada)

        entradas.sort(key=lambda e: e.get("fecha", 0), reverse=True)
        return entradas

    def _tamano(self, entry_id: str) -> int | None:
        ruta = self.ruta_video_guardado(entry_id)
        if ruta is None:
            return None
        try:
            return os.path.getsize(ruta)
        except OSError:
            return None

    def obtener(self, entry_id: str) -> dict | None:
        if not es_id_valido(entry_id):
            return None

        ruta_meta = self._ruta_meta(entry_id)
        if not os.path.exists(ruta_meta):
            return None
        try:
            with open(ruta_meta) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

    def ruta_video_guardado(self, entry_id: str) -> str | None:
        if not es_id_valido(entry_id):
            return None

        ruta = self._ruta_video(entry_id)
        return ruta if os.path.exists(ruta) else None

    def eliminar(self, entry_id: str) -> bool:
        if not es_id_valido(entry_id):
            return False

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
