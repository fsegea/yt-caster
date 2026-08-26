import asyncio

from app.config import Config
from app.state import EstadoApp


class ChromecastService:
    def __init__(self, config: Config, estado: EstadoApp):
        self.config = config
        self.estado = estado

    async def ejecutar(self, comando: str, *args: str) -> None:
        ip = self.estado.get_chromecast_ip()
        proc = await asyncio.create_subprocess_exec(
            "catt", "-d", ip, comando, *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            detalle = stderr.decode(errors="replace").strip()
            print(f"catt {comando} falló (código {proc.returncode}): {detalle}", flush=True)