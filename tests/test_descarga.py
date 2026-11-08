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


def _comando_de_descarga(config: Config, tmp_path) -> list[str]:
    """Devuelve el argv con el que DescargaService invoca yt-dlp."""
    estado = EstadoApp(ip_chromecast="10.0.0.1")
    servicio = DescargaService(config, estado)
    estado.actualizar("job1", "https://example.com/v", "descargando", "...")

    proc = ProcesoFalso(returncode=0)
    comandos: list[list[str]] = []

    async def crear_proceso(*args, **kwargs):
        comandos.append(list(args))
        (tmp_path / "video.mp4").write_bytes(b"datos")
        return proc

    with patch(
        "app.services.download.asyncio.create_subprocess_exec",
        side_effect=crear_proceso,
    ):
        asyncio.run(servicio.descargar("https://example.com/v", "job1"))

    return comandos[0]


def test_comando_de_descarga_usa_el_player_client_por_defecto(tmp_path):
    """Regresión: `tv_base` es el cliente por defecto desde v1.4.1.

    Con `android`, YouTube solo exponia el formato progresivo 18 y cortaba ese
    unico flujo a ~700 KB en videos largos. `tv_base` si expone el ladder DASH
    (136+140) que el selector de formato prefiere, y eso exige ffmpeg para fusionar.
    """
    cmd = _comando_de_descarga(
        Config(descargas_dir=str(tmp_path), chromecast_ip="10.0.0.1"), tmp_path
    )
    i = cmd.index("--extractor-args")
    assert cmd[i + 1] == "youtube:player_client=tv_base"


def test_player_client_se_puede_sobrescribir(tmp_path):
    """El cliente es configuable: admite una lista separada por comas."""
    cmd = _comando_de_descarga(
        Config(
            descargas_dir=str(tmp_path),
            chromecast_ip="10.0.0.1",
            yt_dlp_player_client="tv_base,android",
        ),
        tmp_path,
    )
    i = cmd.index("--extractor-args")
    assert cmd[i + 1] == "youtube:player_client=tv_base,android"


def test_player_client_lecturado_del_entorno(monkeypatch):
    monkeypatch.setenv("YT_DLP_PLAYER_CLIENT", "android")
    assert Config().yt_dlp_player_client == "android"


def test_selector_de_formato_prefiere_avc1_mas_m4a(tmp_path):
    """El selector debe seguir pidiendo video+audio decodificables en el navegador."""
    cmd = _comando_de_descarga(
        Config(descargas_dir=str(tmp_path), chromecast_ip="10.0.0.1"), tmp_path
    )
    i = cmd.index("-f")
    assert cmd[i + 1] == (
        "bestvideo[height<=720][vcodec^=avc1]+bestaudio[acodec^=mp4a]"
        "/best[height<=720]"
    )
    assert cmd[cmd.index("--merge-output-format") + 1] == "mp4"


def _descarga_con_residuos(tmp_path, residuos: list[str]) -> dict[str, list[str]]:
    """Ejecuta una descarga dejando residuos antes de arrancar.

    Devuelve el contenido de `descargas_dir` (rutas relativas) justo antes de invocar
    yt-dlp y al terminar.
    """
    config = Config(descargas_dir=str(tmp_path), chromecast_ip="10.0.0.1")
    estado = EstadoApp(ip_chromecast="10.0.0.1")
    servicio = DescargaService(config, estado)
    estado.actualizar("job1", "https://example.com/v", "descargando", "...")

    for nombre in residuos:
        ruta = tmp_path / nombre
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_bytes(b"restos")

    def listar() -> list[str]:
        return sorted(
            str(p.relative_to(tmp_path))
            for p in tmp_path.rglob("*")
            if p.is_file()
        )

    proc = ProcesoFalso(returncode=0, stdout=(b"[download] 100% of 1.00MiB\n",))
    snapshot: dict[str, list[str]] = {}

    async def crear_proceso(*args, **kwargs):
        snapshot["antes"] = listar()
        (tmp_path / "video.mp4").write_bytes(b"datos")
        return proc

    with patch(
        "app.services.download.asyncio.create_subprocess_exec",
        side_effect=crear_proceso,
    ):
        asyncio.run(servicio.descargar("https://example.com/v", "job1"))

    snapshot["despues"] = listar()
    return snapshot


def test_residuos_de_un_fallo_previo_se_limpian_antes_de_descargar(tmp_path):
    """Regresión: un `video.mp4.part` de un fallo anterior hacia que yt-dlp
    reintentara desde ese offset en la descarga siguiente (de OTRO video) y YouTube
    respondiera `HTTP Error 416: Requested range not satisfiable`.
    """
    residuos = [
        "video.mp4.part",
        "video.mp4.part-Frag1.part",
        "video.f136.mp4.part",
        "video.f136.mp4",
        "video.f140-1.m4a.part",
        "video.info.json",
    ]
    snapshot = _descarga_con_residuos(tmp_path, residuos)

    # Nada mas entrar en yt-dlp ya no queda ni un `.part` que reanudar.
    assert snapshot["antes"] == []
    assert snapshot["despues"] == ["video.mp4"]


def test_limpiar_residuos_no_toca_el_historico_ni_otros_ficheros(tmp_path):
    """La limpieza solo alcanza a `video.*`: lo demas del volumen es ajeno."""
    ajenos = [
        "historico/abc123.mp4",
        "historico/abc123.json",
        "otros.mp4",
        "otros.mp4.part",
    ]
    snapshot = _descarga_con_residuos(tmp_path, ajenos + ["video.mp4.part"])

    for nombre in ajenos:
        assert nombre in snapshot["antes"]
        assert nombre in snapshot["despues"]
    assert "video.mp4.part" not in snapshot["antes"]


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