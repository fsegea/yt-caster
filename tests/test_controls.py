def test_play(client, app):
    ruta = app.state.config.ruta_video
    r = client.post("/play")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
    assert app.state.chromecast_service.calls == [("cast", (ruta,))]


def test_stop(client, app):
    r = client.post("/stop")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
    assert app.state.chromecast_service.calls == [("stop", ())]


def test_pause(client, app):
    r = client.post("/pause")
    assert r.status_code == 200
    assert app.state.chromecast_service.calls == [("pause", ())]


def test_play_toggle(client, app):
    r = client.post("/play-toggle")
    assert r.status_code == 200
    assert app.state.chromecast_service.calls == [("play_toggle", ())]


def test_volumeup_por_defecto(client, app):
    r = client.post("/volumeup")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "delta": 10}
    assert app.state.chromecast_service.calls == [("volumeup", ("10",))]


def test_volumeup_con_delta(client, app):
    r = client.post("/volumeup", json={"delta": 20})
    assert r.json() == {"status": "ok", "delta": 20}
    assert app.state.chromecast_service.calls == [("volumeup", ("20",))]


def test_volumedown(client, app):
    r = client.post("/volumedown", json={"delta": 5})
    assert r.json() == {"status": "ok", "delta": 5}
    assert app.state.chromecast_service.calls == [("volumedown", ("5",))]


def test_ffwd_por_defecto(client, app):
    r = client.post("/ffwd")
    assert r.json() == {"status": "ok", "time": 30}
    assert app.state.chromecast_service.calls == [("ffwd", ("30",))]


def test_ffwd_con_tiempo(client, app):
    r = client.post("/ffwd", json={"time": 60})
    assert r.json() == {"status": "ok", "time": 60}
    assert app.state.chromecast_service.calls == [("ffwd", ("60",))]


def test_rewind(client, app):
    r = client.post("/rewind", json={"time": 15})
    assert r.json() == {"status": "ok", "time": 15}
    assert app.state.chromecast_service.calls == [("rewind", ("15",))]


def test_seek(client, app):
    r = client.post("/seek", json={"time": "01:23:45"})
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "time": "01:23:45"}
    assert app.state.chromecast_service.calls == [("seek", ("01:23:45",))]


def test_seek_sin_cuerpo(client):
    r = client.post("/seek")
    assert r.status_code == 422