# yt-caster

API (FastAPI) que descarga vídeos de YouTube con `yt-dlp` y los reproduce en un Chromecast, con frontend web y controles de reproducción.

## Funcionalidad

- Descarga un vídeo de YouTube a partir de su URL (en segundo plano).
- Lo reproduce en un Chromecast (IP configurable).
- Controles de reproducción: play, stop, pause, volumen, avance/retroceso, seek.
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

## Variables de entorno

| Variable | Por defecto | Descripción |
|----------|-------------|-------------|
| `CHROMECAST_IP` | `10.10.0.44` | IP del Chromecast |
| `DESCARGAS_DIR` | `/descargas` | Directorio donde se guardan los vídeos |

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
  routers/         # Rutas (frontend, salud, descarga, chromecast, controles)
  services/        # Lógica (descarga yt-dlp, control Chromecast)
static/            # Frontend web
tests/             # Tests pytest
```
