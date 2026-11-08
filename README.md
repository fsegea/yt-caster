# yt-caster

API (FastAPI) que descarga vídeos de YouTube con `yt-dlp` y los reproduce en un Chromecast, con frontend web y controles de reproducción.

## Funcionalidad

- Descarga un vídeo de YouTube a partir de su URL (en segundo plano).
- Lo reproduce en un Chromecast (IP configurable).
- Controles de reproducción: play, stop, pause, volumen, avance/retroceso, seek.
- Histórico de vídeos descargados: guardar, listar, reproducir y eliminar.
- **Descarga al cliente**: envía al navegador un vídeo ya descargado en el servidor (el actual o cualquiera del histórico), sin volver a buscarlo a YouTube.
- **Ver en el navegador**: reproduce ese mismo vídeo en una tarjeta `<video>` de la propia página, sin bajarlo a disco y sin pasar por el Chromecast.
- Frontend web en `static/index.html`.
- Healthcheck y versión.

## Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/` | Frontend web |
| `GET` | `/salud` | Healthcheck |
| `GET` | `/version` | Versión actual |
| `POST` | `/descargar` | `{url}` — descarga el vídeo en segundo plano, devuelve `job_id` |
| `GET` | `/estado` | Estado de la descarga actual |
| `GET` | `/video` | Descarga en el cliente el vídeo descargado actualmente en el servidor |
| `GET` | `/video/ver` | Sirve ese vídeo en línea (`inline`) para reproducirlo en el navegador |
| `GET` | `/video/info` | `{disponible, nombre, tamano}` del vídeo disponible para descargar |
| `GET` | `/chromecast` | IP del Chromecast configurada |
| `POST` | `/chromecast` | `{ip}` — cambia la IP del Chromecast |
| `POST` | `/play` | Reproducir |
| `POST` | `/stop` | Detener |
| `POST` | `/pause` | Pausar |
| `POST` | `/play-toggle` | Alternar play/pause |
| `POST` | `/volumeup` | `{delta}` (1-100, por defecto 10) |
| `POST` | `/volumedown` | `{delta}` (1-100, por defecto 10) |
| `POST` | `/ffwd` | `{time}` segundos (por defecto 30) |
| `POST` | `/rewind` | `{time}` segundos (por defecto 30) |
| `POST` | `/seek` | `{time}` posición absoluta |
| `POST` | `/historico` | Guarda el vídeo descargado actualmente en el histórico |
| `GET` | `/historico` | Lista los vídeos guardados (`{videos: [...]}`) |
| `GET` | `/historico/{entry_id}/descargar` | Descarga en el cliente un vídeo del histórico |
| `GET` | `/historico/{entry_id}/ver` | Reproduce en el navegador un vídeo del histórico |
| `POST` | `/historico/{entry_id}/play` | Reproduce un vídeo del histórico en el Chromecast |
| `DELETE` | `/historico/{entry_id}` | Elimina un vídeo del histórico |

## Variables de entorno

| Variable | Por defecto | Descripción |
|----------|-------------|-------------|
| `CHROMECAST_IP` | `10.10.0.44` | IP del Chromecast |
| `DESCARGAS_DIR` | `/descargas` | Directorio donde se guardan los vídeos |
| `YT_DLP_PLAYER_CLIENT` | `tv_base` | Cliente de YouTube que usa `yt-dlp` (`youtube:player_client=...`) |
| `YT_DLP_ACTUALIZAR` | `0` | Si vale `1`, el contenedor instala la última `yt-dlp` al arrancar |

## Ejecución

### Desarrollo (hot reload)

```bash
podman-compose up -d --build
```

### Producción

```bash
podman-compose -f compose.prod.yaml up -d --build
```

### Portainer

Usa `stack.portainer.yaml`, que refleja el despliegue real. La imagen se referencia
**por versión** (`fsegea/yt-caster:v1.4.0`), nunca con `latest`.

## Versión de Python

La versión soportada es **3.12 o 3.13** (`requires-python = ">=3.12,<3.14"`). Lo que
corre en producción es lo que declara `pyproject.toml`, y está declarado en un solo sitio
para que no vuelva a divergir:

| Dónde | Versión |
|-------|---------|
| `pyproject.toml` (`requires-python`) | `>=3.12,<3.14` |
| `.python-version` (venv de desarrollo) | `3.13` |
| `Dockerfile.dev` / `Dockerfile.prod` (builder y runtime) | `python:3.13-slim` |
| Matriz de tests del CI | `3.12` y `3.13` |

Hasta `v1.3.1` los contenedores corrían en 3.12 mientras los tests solo se ejecutaban
en el 3.13 del puesto de desarrollo, y el CI no ejecutaba tests: nada garantizaba que la
imagen publicada funcionase en el intérprete en el que corría. Ahora el job `test` es
`needs` obligatorio del job `build`.

## Publicar una versión

1. Cambiar el código y pasar los tests: `pytest`
2. Subir `VERSION` (una línea, p. ej. `v1.3.2`) **y el campo `version` de `pyproject.toml`**
   (el CI aborta si no cuadran)
3. Commitear, taggear y empujar:

```bash
git commit -a -m "v1.3.2: ..."
git tag -a v1.3.2 -m "v1.3.2"
git push origin main --tags
```

4. El CI (`.github/workflows/docker.yml`) ejecuta los tests en 3.12 y 3.13, comprueba que
   `VERSION` y `pyproject.toml` cuadran, y entonces construye y publica. La etiqueta de la
   imagen sale del fichero `VERSION` del commit, no del nombre del tag de git.
5. En Portainer, cambiar la etiqueta en el stack y *Redeploy*.

**Regla: solo el CI publica imágenes.** Nadie hace `docker build` + `docker push` a mano.
Si existe una imagen en Docker Hub, tiene que existir su commit y su tag en GitHub: la
única forma de que vuelva a haber deriva de versiones es saltarse esta regla.

El CI necesita dos secrets en el repositorio (Settings → Secrets and variables → Actions):

| Secret | Valor |
|--------|-------|
| `DOCKERHUB_USERNAME` | `fsegea` |
| `DOCKERHUB_TOKEN` | access token de hub.docker.com, ámbito **Read & Write** |

## Despliegue en producción

Host `vm0` (`10.10.0.100`), gestionado desde Portainer con el stack `yt-endpoint`.
El fichero vivo es `stack.portainer.yaml`; debe mantenerse idéntico a lo desplegado.

- Imagen fijada a una versión concreta, no `latest`.
- Volumen `yt_descargas` montado en `/descargas`: ahí viven `video.mp4` y `historico/`.
- `CHROMECAST_IP` por defecto `10.10.0.41` (Android TV). `10.10.0.44` es el Chromecast;
  se cambia en caliente con `POST /chromecast`.
- Verificar tras un despliegue:

```bash
curl -s http://10.10.0.100:8000/version
docker inspect yt-caster --format '{{.Config.Image}} {{.Image}}'
```

## Trampas ya sufridas

- **`latest` en el stack**: un redeploy te trae lo que Hub tenga en ese momento, y en
  cambio `docker compose up -d` no vuelve a bajar la imagen si la etiqueta ya existe en
  el host. Fijar la versión evita los dos problemas.
- **Compose puede heredar la spec del contenedor anterior** al recrear (se vio con el
  `CMD` de la imagen vieja sobreviviendo a un cambio de imagen). Si algo no cambia pese
  a redeployar, borra el contenedor y vuelve a desplegar, o cambia algo del compose para
  forzar un `config-hash` nuevo.
- **Dos builds del mismo commit tienen digests distintos** (timestamps y attestation).
  No compares digests entre maquinas: compara etiquetas.
- **`.dockerignore` necesita prefijo `**/`** para los patrones anidados: `__pycache__/`
  solo excluye el de la raiz, no `app/__pycache__`.
- **`yt-dlp` sin fijar** hace que el contenedor cambie de comportamiento en cada arranque
  sin commit ni tag. Ver siguiente apartado.
- **Dos Python conviviendo sin declararlo**: el venv local era 3.13 y los contenedores
  3.12. Como `compose.yaml` monta `./app:/app/app`, el contenedor escribía
  `app/__pycache__/*.cpython-312.pyc` junto a los `*.cpython-313.pyc` del `pytest` local.
  Es inocuo (Python descarta el `.pyc` con magic number ajeno y recompila), pero ensucia
  la imagen y tapaba que los tests no cubrían la versión de producción.
- **`pytest` y `python -m pytest` no son lo mismo**: el script de consola no añade el
  directorio actual a `sys.path`, así que `from app...` en los tests falla con
  `ModuleNotFoundError: No module named 'app'`. En local se colaba porque se ejecutaba
  `python -m pytest`. Lo destapó el CI (v1.3.2, run 2). Queda resuelto con
  `pythonpath = ["."]` en `pyproject.toml`.
- **`player_client=android` con vídeos largos**: ese cliente solo exponía el formato
  progresivo `18`, y YouTube cortaba ese flujo único a ~700 KB (`Got error: 0 bytes read,
  10 MB more expected`, 10 reintentos y `La descarga falló`). Los vídeos cortos pasaban,
  así que el fallo parecía intermitente. Desde v1.4.1 el cliente es configurable y por
  defecto `tv_base`, que sí expone el ladder DASH (`136+140`) y baja los 255 MB de un
  vídeo de 31 minutos sin problemas. Ver apartado *Cliente de YouTube*.
- **Un `.part` huérfano envenenaba la descarga siguiente**: tras un fallo se quedaban
  `video.mp4.part` (y `video.f136.mp4.part`, `video.info.json`) en `/descargas`, y
  `_borrar_video_si_existe()` solo limpiaba `video.mp4` y `video.info.json`. Como el
  nombre de salida es siempre el mismo, `yt-dlp` reanudaba desde ese offset aunque el
  vídeo nuevo fuera otro: `[download] Resuming download at byte 653312` seguido de
  `HTTP Error 416: Requested range not satisfiable`. Desde v1.4.1 la limpieza alcanza a
  `video*.part`, `video*.part-Frag*`, `video*.ytdl` y `video.f*`, y no toca `historico/`.

## Versionar yt-dlp

`yt-dlp` va **fijado** en `requirements.txt` (ahora mismo `2026.10.26`), así que la
versión empaquetada queda ligada a un commit y a un tag de la imagen: dos despliegues
del mismo tag son iguales.

Cuando YouTube rompa un extractor y haga falta subir la versión:

```bash
sed -i 's/yt-dlp==.*/yt-dlp==2026.11.11/' requirements.txt
pytest
```

Y luego se sigue el flujo normal de *Publicar una versión* (subir `VERSION`, commitear,
tagear y empujar).

Si hace falta un apaño urgente sin reconstruir la imagen, arranca el contenedor con
`YT_DLP_ACTUALIZAR=1` para que instale la última versión al levantar. Es la vía rápida
y no auditable: úsala solo como parche temporal y luego fija el pin en un commit.

## Cliente de YouTube (`player_client`)

`DescargaService` pasa `--extractor-args youtube:player_client=<cliente>` con el valor
de `YT_DLP_PLAYER_CLIENT`, por defecto **`tv_base`** (desde v1.4.1; antes estaba fijado
a `android`).

Importa porque cada cliente ve un inventario distinto de formatos y **solo algunos
devuelven URLs usable**s:

| Cliente | Qué expone |
|---------|------------|
| `tv_base` | ladder DASH completo: `136` (720p `avc1`) + `140` (`m4a`), `134`, `160`, `249/250`… |
| `android` | el progresivo `18` (360p, un único flujo) y nada más |
| `web`, `mweb`, `ios`, `android_vr` | nada descargable sin PO token / por el experimento SABR-only |

El selector de formato prefiere `bestvideo[height<=720][vcodec^=avc1]+bestaudio[acodec^=mp4a]`,
que **solo es realizable con un cliente que exponga DASH**: con `android` caía siempre al
fallback `best[height<=720]` = `18`. Fusionar esas dos pistas requiere `ffmpeg`, que ya
instalan `Dockerfile.dev` y `Dockerfile.prod`; en el venv del host hay que tenerlo a mano
(`ffdl install`, `apt install ffmpeg`…). Sin `ffmpeg`, `yt-dlp` descarta el `136+140` y
vuelve al progresivo.

Se puede cambiar sin tocar código, admitiendo lista separada por comas:

```bash
YT_DLP_PLAYER_CLIENT=tv_base,android   # prueba varios clientes y mezcla formatos
```

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

El CI ejecuta esos mismos tests en Python 3.12 y 3.13 en cada tag, en cada PR y en cada
`workflow_dispatch`, y no publica la imagen si alguno falla.

## Estructura

```
app/
  main.py          # App FastAPI
  config.py        # Configuración (pydantic-settings)
  state.py         # Estado en memoria
  models.py        # Modelos Pydantic
  deps.py          # Dependencias
  routers/         # Rutas (frontend, salud, descarga, chromecast, controles, histórico)
  services/        # Lógica (descarga yt-dlp, control Chromecast, histórico, ficheros descargables)
  responses.py     # Respuestas de vídeo al cliente (inline / attachment)
static/            # Frontend web
tests/             # Tests pytest
AGENTS.md          # Reglas del repo para herramientas de desarrollo (pi lo carga solo)
pyproject.toml     # requires-python y version (debe cuadrar con VERSION)
.python-version    # 3.13: version del venv de desarrollo
stack.portainer.yaml   # Stack de Portainer (despliegue real)
.github/workflows/docker.yml  # CI: tests 3.12+3.13 -> tag -> imagen en Docker Hub
```

## Descargar o ver en el navegador

`GET /video` y `GET /historico/{entry_id}/descargar` devuelven el fichero con
`Content-Disposition: attachment`, así que el navegador lo guarda sin recargarlo
desde YouTube. El nombre se deriva del título del vídeo, sanitizado (sin acentos
ni caracteres problemáticos).

`GET /video/ver` y `GET /historico/{entry_id}/ver` devuelven el mismo fichero con
`Content-Disposition: inline`: el navegador lo reproduce en la tarjeta «Ver en el
navegador» de la página en lugar de guardarlo. En el histórico hay un botón «Ver»
por vídeo; para el vídeo actual, el botón «Ver en el navegador» aparece junto al de
descarga cuando `GET /video/info` informa de uno disponible.

Las cuatro rutas aceptan `Range` (responden `206` con `Content-Range` y anuncian
`Accept-Ranges: bytes`), así que el navegador puede descargar en paralelo y, sobre
todo, buscar (seek) dentro del vídeo sin bajarlo entero. Eso lo resuelve
`FileResponse` de Starlette; `app/responses.py:respuesta_video()` es el único sitio
donde se decide `inline` frente a `attachment`.

Un par de detalles del visor:

- El `src` lleva un `?v=<timestamp>`: `video.mp4` se sobreescribe en cada descarga y
  sin eso el navegador puede seguir mostrando la copia cacheada.
- Si el navegador no puede reproducir el códec aparece un aviso y queda la vía de
  la descarga. Puede pasar con el fallback del selector de formato de `yt-dlp`
  (`best[height<=720]`), que remuxa a MP4 pistas VP9/Opus que no todos los
  navegadores decodifican.
