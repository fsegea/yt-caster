import os

import pytest

from app.config import Config
from app.services.historico import HistoricoService


@pytest.fixture
def servicio(tmp_path):
    config = Config(descargas_dir=str(tmp_path), chromecast_ip="10.0.0.1")
    return HistoricoService(config), config


def _crear_video(config, contenido=b"datos"):
    with open(config.ruta_video, "wb") as f:
        f.write(contenido)


def test_guardar_copia_el_video_y_persiste_metadata(servicio):
    historico, config = servicio
    _crear_video(config)

    entrada = historico.guardar("http://u", "Mi vídeo", config.ruta_video)

    assert entrada["titulo"] == "Mi vídeo"
    assert entrada["url"] == "http://u"
    assert "id" in entrada and "fecha" in entrada
    assert os.path.exists(f"{config.historico_dir}/{entrada['id']}.mp4")
    assert os.path.exists(f"{config.historico_dir}/{entrada['id']}.json")

    # El video original sigue existiendo (se copia, no se mueve)
    assert os.path.exists(config.ruta_video)


def test_guardar_sin_video_lanza_error(servicio):
    historico, config = servicio
    with pytest.raises(FileNotFoundError):
        historico.guardar("http://u", "titulo", config.ruta_video)


def test_guardar_usa_url_si_no_hay_titulo(servicio):
    historico, config = servicio
    _crear_video(config)
    entrada = historico.guardar("http://u", "", config.ruta_video)
    assert entrada["titulo"] == "http://u"


def test_listar_vacio(servicio):
    historico, _ = servicio
    assert historico.listar() == []


def test_listar_ordena_por_fecha_desc(servicio):
    historico, config = servicio
    _crear_video(config)
    e1 = historico.guardar("http://u1", "uno", config.ruta_video)
    e1["fecha"] = 100
    historico._asegurar_dir()
    import json
    with open(historico._ruta_meta(e1["id"]), "w") as f:
        json.dump(e1, f)

    e2 = historico.guardar("http://u2", "dos", config.ruta_video)
    e2["fecha"] = 200
    with open(historico._ruta_meta(e2["id"]), "w") as f:
        json.dump(e2, f)

    listado = historico.listar()
    assert [v["id"] for v in listado] == [e2["id"], e1["id"]]


def test_eliminar(servicio):
    historico, config = servicio
    _crear_video(config)
    entrada = historico.guardar("http://u", "titulo", config.ruta_video)

    assert historico.eliminar(entrada["id"]) is True
    assert historico.obtener(entrada["id"]) is None
    assert historico.ruta_video_guardado(entrada["id"]) is None


def test_eliminar_inexistente(servicio):
    historico, _ = servicio
    assert historico.eliminar("no-existe") is False


def test_ruta_video_guardado(servicio):
    historico, config = servicio
    _crear_video(config)
    entrada = historico.guardar("http://u", "titulo", config.ruta_video)
    assert historico.ruta_video_guardado(entrada["id"]) == f"{config.historico_dir}/{entrada['id']}.mp4"
    assert historico.ruta_video_guardado("no-existe") is None
