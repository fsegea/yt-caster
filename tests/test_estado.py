from app.state import EstadoApp


def test_actualizar_y_obtener():
    e = EstadoApp(ip_chromecast="1.1.1.1")
    e.actualizar("abc", "http://u", "descargando", "Descargando video...")
    estado = e.get_estado()
    assert estado["id"] == "abc"
    assert estado["url"] == "http://u"
    assert estado["estado"] == "descargando"
    assert estado["mensaje"] == "Descargando video..."
    assert "iniciado_at" in estado and "actualizado_at" in estado


def test_es_job_activo():
    e = EstadoApp(ip_chromecast="1.1.1.1")
    e.actualizar("a", "u", "descargando")
    assert e.es_job_activo("a")
    assert not e.es_job_activo("b")


def test_ip_chromecast():
    e = EstadoApp(ip_chromecast="1.1.1.1")
    assert e.get_chromecast_ip() == "1.1.1.1"
    e.set_chromecast_ip("2.2.2.2")
    assert e.get_chromecast_ip() == "2.2.2.2"


def test_limpiar_proceso_solo_si_es_el_mismo():
    e = EstadoApp(ip_chromecast="1.1.1.1")
    viejo = object()
    nuevo = object()
    e.set_proceso(viejo)
    e.limpiar_proceso(nuevo)
    assert e.get_proceso() is viejo
    e.limpiar_proceso(viejo)
    assert e.get_proceso() is None