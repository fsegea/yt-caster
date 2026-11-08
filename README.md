# yt-caster

API (FastAPI) que descarga vídeos de YouTube con `yt-dlp` y los reproduce en un Chromecast, con frontend web y controles de reproducción.

## Funcionalidad

- Descarga un vídeo de YouTube a partir de su URL (en segundo plano).
- Lo reproduce en un Chromecast (IP configurable).
- Controles de reproducción: play, stop, pause, volumen, avance/retroceso, seek.
- Histórico de vídeos descargados: guardar, listar, reproducir y eliminar.
- **Descarga al cliente**: envía al navegador un vídeo ya descargado en el servidor (el actual o cualquiera del histórico), sin volver a buscarlo a YouTube.
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
| `POST` | `/historico/{entry_id}/play` | Reproduce un vídeo del histórico en el Chromecast |
| `DELETE` | `/historico/{entry_id}` | Elimina un vídeo del histórico |

## Variables de entorno

| Variable | Por defecto | Descripción |
|----------|-------------|-------------|
| `CHROMECAST_IP` | `10.10.0.44` | IP del Chromecast |
| `DESCARGAS_DIR` | `/descargas` | Directorio donde se guardan los vídeos |
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
**por versión** (`fsegea/yt-caster:v1.3.1`), nunca con `latest`.

## Publicar una versión

1. Cambiar el código y pasar los tests: `pytest`
2. Subir `VERSION` (una línea, p. ej. `v1.3.2`)
3. Commitear, taggear y empujar:

```bash
git commit -a -m "v1.3.2: ..."
git tag -a v1.3.2 -m "v1.3.2"
git push origin main --tags
```

4. El CI (`.github/workflows/docker.yml`) construye y publica. La etiqueta de la imagen
   sale del fichero `VERSION` del commit, no del nombre del tag de git.
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

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

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
static/            # Frontend web
tests/             # Tests pytest
stack.portainer.yaml   # Stack de Portainer (despliegue real)
.github/workflows/docker.yml  # CI: tag -> imagen en Docker Hub
```

## Descargar al cliente

`GET /video` y `GET /historico/{entry_id}/descargar` devuelven el fichero con
`Content-Disposition: attachment`, así que el navegador lo guarda sin recargarlo
desde YouTube. El nombre se deriva del título del vídeo, sanitizado (sin acentos
ni caracteres problemáticos).

Las respuestas aceptan `Range`, así que el navegador puede descargar en paralelo
o reproducir el vídeo mientras se baja. El botón «Descargar a este dispositivo»
aparece en el frontend cuando `GET /video/info` informa de un vídeo disponible.
