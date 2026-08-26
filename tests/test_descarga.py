import asyncio
from unittest.mock import patch

from app.config import Config
from app.services.download import PROGRESO_RE, DescargaService
from app.state import EstadoApp


class FlujoSalida:
    def __init__(self, lineas):
        self._lineas = tuple(lineas)

    def __aiter__(self):
        return self._gen()

    async def _gen(self):
        for l in self._lineas:
            yield l


class ProcesoFalso:
    def __init__(self, returncode=0, stdout=(), stderr=()):
        self.returncode = returncode
        self.pid = 4242
        self._stdout = FlujoSalida(stdout)
        self._stderr = FlujoSalida(stderr)

    @property
    def stdout(self):
        return FlujoSalida(self._stdout._lineas)

    @property
    def stderr(self):
        return FlujoSalida(self._stderr._lineas)

    async def wait(self):
        return self.returncode if self.returncode is not None else 0


def probar_descarga(tmp_path, *, returncode=0, crear_video=True, stdout=()):
    config = Config(descargas_dir=str(tmp_path), chromecast_ip="10.0.0.1")
    estado = EstadoApp(ip_chromecast="10.0.0.1")
    servicio = DescargaService(config, estado)
    job_id = "job1"
    url = "https://example.com/v"
    estado.actualizar(job_id, url, "descargando", "Descargando video...")

    proc = ProcesoFalso(returncode=returncode, stdout=stdout)

    async def crear_proceso(*args, **kwargs):
        if crear_video:
            (tmp_path / "video.mp4").write_bytes(b"datos")
        return proc

    with patch(
        "app.services.download.asyncio.create_subprocess_exec",
        side_effect=crear_proceso,
    ):
        asyncio.run(servicio.descargar(url, job_id))
    return estado, proc


def test_descarga_correcta(tmp_path):
    estado, proc = probar_descarga(
        tmp_path, stdout=(b"[download] 100% of 1.00MiB\n",)
    )
    assert proc.returncode == 0
    assert estado.get_estado()["estado"] == "correcto"
    assert estado.get_estado()["mensaje"] == "Descarga completada"


def test_descarga_error_por_returncode(tmp_path):
    estado, _ = probar_descarga(tmp_path, returncode=1, crear_video=False)
    assert estado.get_estado()["estado"] == "error"
    assert estado.get_estado()["mensaje"] == "La descarga falló"


def test_descarga_error_sin_video(tmp_path):
    estado, _ = probar_descarga(tmp_path, returncode=0, crear_video=False)
    assert estado.get_estado()["estado"] == "error"
    assert (
        estado.get_estado()["mensaje"] == "No se encontró el video tras la descarga"
    )


def test_progreso_se_reconoce():
    m = PROGRESO_RE.search("[download]  12.5% of 10.00MiB at 2.00MiB/s")
    assert m is not None
    assert m.group(1) == "12.5"


def test_descarga_ignorada_si_job_no_activo(tmp_path):
    config = Config(descargas_dir=str(tmp_path), chromecast_ip="10.0.0.1")
    estado = EstadoApp(ip_chromecast="10.0.0.1")
    servicio = DescargaService(config, estado)
    estado.actualizar("otro_job", "http://otra", "descargando", "...")

    with patch(
        "app.services.download.asyncio.create_subprocess_exec"
    ) as mock:
        asyncio.run(servicio.descargar("http://mi", "mi_job"))
        mock.assert_not_called()

    assert estado.get_estado()["id"] == "otro_job"
    assert estado.es_job_activo("otro_job")


def test_nueva_descarga_mata_anterior(tmp_path):
    config = Config(descargas_dir=str(tmp_path), chromecast_ip="10.0.0.1")
    estado = EstadoApp(ip_chromecast="10.0.0.1")
    servicio = DescargaService(config, estado)

    proc_viejo = ProcesoFalso(returncode=None)
    estado.set_proceso(proc_viejo)

    proc_nuevo = ProcesoFalso(returncode=0, stdout=(b"[download] 100% of 1.00MiB\n",))

    async def crear_proceso(*args, **kwargs):
        (tmp_path / "video.mp4").write_bytes(b"datos")
        return proc_nuevo

    estado.actualizar("nuevo_job", "http://nueva", "descargando", "...")

    with patch(
        "app.services.download.asyncio.create_subprocess_exec",
        side_effect=crear_proceso,
    ) as mock, patch(
        "app.services.download.os.getpgid", return_value=12345
    ) as mock_getpgid, patch(
        "app.services.download.os.killpg"
    ) as mock_killpg:
        asyncio.run(servicio.descargar("http://nueva", "nuevo_job"))

        mock.assert_called_once()
        mock_getpgid.assert_called_once_with(4242)
        assert mock_killpg.call_count >= 1
        assert estado.get_proceso() is None
        assert estado.get_estado()["estado"] == "correcto"