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

Usa `stack.portainer.yaml` (o la imagen `fsegea/yt-caster` en Docker Hub).

## Versionar yt-dlp

`yt-dlp` va **fijado** en `requirements.txt` (ahora mismo `2026.10.26`), así que la
versión empaquetada queda ligada a un commit y a un tag de la imagen: dos despliegues
del mismo tag son iguales.

Cuando YouTube rompa un extractor y haga falta subir la versión:

```bash
# 1. subir el pin y comprobar que descarga
sed -i 's/yt-dlp==.*/yt-dlp==2026.11.11/' requirements.txt
pytest

# 2. versionar, commitear, taggear y publicar
git commit -a -m "yt-dlp 2026.11.11"
git tag -a v1.3.2 -m "yt-dlp 2026.11.11"
git push origin main --tags
```

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
```

## Descargar al cliente

`GET /video` y `GET /historico/{entry_id}/descargar` devuelven el fichero con
`Content-Disposition: attachment`, así que el navegador lo guarda sin recargarlo
desde YouTube. El nombre se deriva del título del vídeo, sanitizado (sin acentos
ni caracteres problemáticos).

Las respuestas aceptan `Range`, así que el navegador puede descargar en paralelo
o reproducir el vídeo mientras se baja. El botón «Descargar a este dispositivo»
aparece en el frontend cuando `GET /video/info` informa de un vídeo disponible.
