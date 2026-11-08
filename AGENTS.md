# yt-caster — notas para trabajar en este repo

API FastAPI que descarga vídeos de YouTube con `yt-dlp` y los reproduce en un Chromecast.
Produccion en `vm0` (`10.10.0.100`), gestionada con Portainer (stack `yt-endpoint`).
El README es la fuente larga; aqui solo las reglas que hay que cumplir sin discutir.

## Version de Python

- Soportada: **3.12 y 3.13** (`requires-python = ">=3.12,<3.14"` en `pyproject.toml`).
- Ejecutada en produccion y desarrollo contenerizado: **3.13** (`python:3.13-slim`).
- Venv local: **3.13** (`.python-version`).
- Fuentes que deben cuadrar: `pyproject.toml`, `.python-version`, `Dockerfile.dev`,
  `Dockerfile.prod` (builder Y runtime) y la matriz del CI.
- No anadir sintaxis exclusiva de 3.13 sin subir antes la base de los Dockerfiles.

## Versionar y publicar

- `VERSION` (p. ej. `v1.3.2`) y el campo `version` de `pyproject.toml` (`1.3.2`) suben
  **juntos**. El CI aborta el job `build` si no cuadran.
- La etiqueta de la imagen sale de `VERSION`, no del nombre del tag de git.
- **Solo el CI publica imagenes.** Nadie hace `docker build` + `docker push` a mano.
  Flujo: subir version -> commit -> `git tag -a vX.Y.Z` -> `git push origin main --tags`.
- El job `test` (matriz 3.12 + 3.13) es `needs` obligatorio de `build`: si un test falla,
  no se publica nada.
- Si hace falta corregir algo despues de tagear y el `build` no llego a publicar, mover el
  tag es legitimo: `git tag -a -f vX.Y.Z && git push -f origin refs/tags/vX.Y.Z`.

## Tests

- `pytest` a secas funciona (esta `pythonpath = ["."]` en `pyproject.toml`). No usar
  `python -m pytest` como referencia: el script de consola y el modulo resuelven
  `sys.path` distinto, y esa diferencia fue la que rompio el CI en v1.3.2.
- Los tests son hermeticos: `tmp_path` + fakes en `tests/conftest.py`. No deben tocar red
  ni Chromecast. Si alguno necesita red, es un bug.

## yt-dlp

- Fijada en `requirements.txt` (`yt-dlp==YYYY.M.D`). Subirla va con commit y tag.
- `YT_DLP_ACTUALIZAR=1` es un apaño temporal y no auditable: no dejarlo en el stack.
- El cliente de YouTube es `YT_DLP_PLAYER_CLIENT`, por defecto `tv_base`. No volver a
  `android`: solo exponía el progresivo 18 y YouTube cortaba ese flujo en vídeos largos.
- Fusionar pistas DASH necesita `ffmpeg` (los Dockerfiles lo instalan; en el venv del host
  hay que instalarlo a mano). Sin `ffmpeg` el selector cae al fallback progresivo.
- La limpieza previa de `/descargas` debe borrar tambien `video*.part` y `video.f*`: un
  residuo hace que la descarga siguiente falle con `HTTP 416`.

## Despliegue

- Fichero vivo: `stack.portainer.yaml`. Debe mantenerse identico a lo desplegado.
- Imagen **siempre fijada a una version**, nunca `latest`.
- Tras un redeploy, verificar: `curl -s http://10.10.0.100:8000/version`.
- `CHROMECAST_IP` por defecto `10.10.0.41` (Android TV); `10.10.0.44` es el Chromecast.
- El socket de Docker no esta disponible desde el entorno de desarrollo: no intentar
  `docker ps` / `docker build` aqui; la validacion de imagen la hace el CI.

## Trampas ya pagadas (detalle completo en el README)

- `latest` en el stack + `compose up` que no vuelve a bajar la imagen.
- Compose heredando la spec del contenedor anterior al recrear.
- Digests distintos para dos builds del mismo commit: comparar etiquetas, no digests.
- `.dockerignore` necesita prefijo `**/` para patrones anidados.
- Dos Python conviviendo sin declararlo (venv 3.13 vs contenedores 3.12).
- `pytest` vs `python -m pytest` y el paquete `app` en `sys.path`.
