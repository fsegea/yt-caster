import pytest

from app.config import Config
from app.services.archivo import ArchivoService, LONGITUD_MAXIMA_NOMBRE
from app.services.historico import HistoricoService


@pytest.fixture
def servicio(tmp_path):
    config = Config(descargas_dir=str(tmp_path), chromecast_ip="10.0.0.1")
    historico = HistoricoService(config)
    return ArchivoService(config, historico), historico, config


def _crear_video(config, contenido=b"datos"):
    with open(config.ruta_video, "wb") as f:
        f.write(contenido)


def test_video_actual_inexistente(servicio):
    archivo, _, config = servicio
    assert archivo.video_actual("Mi vídeo") is None


def test_video_actual_resuelve_ruta_nombre_y_tamano(servicio):
    archivo, _, config = servicio
    _crear_video(config, b"123456")

    resultado = archivo.video_actual("Mi vídeo")

    assert resultado is not None
    assert resultado.ruta == config.ruta_video
    assert resultado.nombre == "Mi_video.mp4"
    assert resultado.tamano == 6


def test_video_actual_sin_titulo_usa_nombre_generico(servicio):
    archivo, _, config = servicio
    _crear_video(config)

    assert archivo.video_actual("").nombre == "video.mp4"


def test_video_historico(servicio):
    archivo, historico, config = servicio
    _crear_video(config, b"12345")
    entrada = historico.guardar("http://u", "Vídeo guardado", config.ruta_video)

    resultado = archivo.video_historico(entrada["id"])

    assert resultado is not None
    assert resultado.nombre == "Video_guardado.mp4"
    assert resultado.tamano == 5
    assert resultado.ruta.endswith(f"{entrada['id']}.mp4")


def test_video_historico_inexistente(servicio):
    archivo, _, _ = servicio
    assert archivo.video_historico("a" * 32) is None


def test_video_historico_sin_fichero_de_video(servicio):
    import os

    archivo, historico, config = servicio
    _crear_video(config)
    entrada = historico.guardar("http://u", "titulo", config.ruta_video)
    os.remove(archivo.video_historico(entrada["id"]).ruta)

    assert archivo.video_historico(entrada["id"]) is None

@pytest.mark.parametrize("entry_id", ["", "..", "../../etc/passwd", "no-existe", "a" * 65])
def test_video_historico_rechaza_ids_malformados(servicio, entry_id):
    archivo, _, _ = servicio
    assert archivo.video_historico(entry_id) is None


@pytest.mark.parametrize(
    "titulo,esperado",
    [
        ("Mi vídeo", "Mi_video.mp4"),
        ("Mi/vídeo: #1", "Mi_video_1.mp4"),
        ("..", "video.mp4"),
        ("", "video.mp4"),
        ("   ", "video.mp4"),
        ("中文", "video.mp4"),
        ("Hola\tMundo", "Hola_Mundo.mp4"),
        ("Sin extensión.mp4", "Sin_extension.mp4.mp4"),
    ],
)
def test_nombre_archivo_sanitiza_titulos(titulo, esperado):
    assert ArchivoService.nombre_archivo(titulo) == esperado


def test_nombre_archivo_limita_longitud():
    nombre = ArchivoService.nombre_archivo("a" * 300)
    assert nombre == f"{'a' * LONGITUD_MAXIMA_NOMBRE}.mp4"
