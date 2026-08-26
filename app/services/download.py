import asyncio
import json
import os
import re
import signal
import sys

from app.config import Config
from app.state import EstadoApp

PROGRESO_RE = re.compile(r"\[download\]\s+(\d+(?:\.\d+)?)%")


class DescargaService:
    def __init__(self, config: Config, estado: EstadoApp):
        self.config = config
        self.estado = estado

    async def _matar_proceso_actual(self) -> None:
        proc = self.estado.get_proceso()
        if proc is not None and proc.returncode is None:
            try:
                pgid = os.getpgid(proc.pid)
            except ProcessLookupError:
                self.estado.limpiar_proceso(proc)
                return
            try:
                os.killpg(pgid, signal.SIGTERM)
                await asyncio.wait_for(proc.wait(), timeout=3)
            except (asyncio.TimeoutError, ProcessLookupError):
                try:
                    os.killpg(pgid, signal.SIGKILL)
                    await proc.wait()
                except Exception:
                    pass
        self.estado.limpiar_proceso(proc)

    def _borrar_video_si_existe(self) -> None:
        if os.path.exists(self.config.ruta_video):
            os.remove(self.config.ruta_video)
        if os.path.exists(self.config.ruta_info):
            os.remove(self.config.ruta_info)

    def _extraer_titulo(self, url: str) -> str:
        try:
            with open(self.config.ruta_info) as f:
                data = json.load(f)
            return data.get("title") or url
        except (FileNotFoundError, json.JSONDecodeError):
            return url
        finally:
            if os.path.exists(self.config.ruta_info):
                os.remove(self.config.ruta_info)

    async def _leer_salida(self, proc, job_id: str, url: str) -> None:
        tarea_stderr = asyncio.create_task(self._leer_stderr(proc))
        try:
            async for linea in proc.stdout:
                texto = linea.decode(errors="replace").strip()
                print(texto, flush=True)
                if self.estado.es_job_activo(job_id):
                    m = PROGRESO_RE.search(texto)
                    if m:
                        self.estado.actualizar(
                            job_id, url, "descargando", f"Descargando {m.group(1)}%"
                        )
        finally:
            await tarea_stderr

    async def _leer_stderr(self, proc) -> str:
        lineas: list[str] = []
        async for linea in proc.stderr:
            texto = linea.decode(errors="replace").strip()
            if texto:
                print(f"yt-dlp stderr: {texto}", flush=True)
                lineas.append(texto)
        return "\n".join(lineas)

    async def descargar(self, url: str, job_id: str) -> None:
        if not self.estado.es_job_activo(job_id):
            return

        await self._matar_proceso_actual()
        self._borrar_video_si_existe()
        self.estado.actualizar(job_id, url, "descargando", "Descargando video...")

        cmd = [
            sys.executable, "-m", "yt_dlp",
            "-f", "bestvideo[height<=720][vcodec^=avc1]+bestaudio[acodec^=mp4a]/best[height<=720]",
            "--merge-output-format", "mp4",
            "-o", self.config.ruta_video,
            "--write-info-json",
            "--newline",
            "--progress",
            "--", url,
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            start_new_session=True,
        )
        self.estado.set_proceso(proc)

        await self._leer_salida(proc, job_id, url)
        await proc.wait()
        self.estado.limpiar_proceso(proc)

        if not self.estado.es_job_activo(job_id):
            return

        if proc.returncode != 0:
            self.estado.actualizar(job_id, url, "error", "La descarga falló")
            return

        if not os.path.exists(self.config.ruta_video):
            self.estado.actualizar(
                job_id, url, "error", "No se encontró el video tras la descarga"
            )
            return

        titulo = self._extraer_titulo(url)
        self.estado.actualizar(job_id, url, "correcto", "Descarga completada", titulo=titulo)