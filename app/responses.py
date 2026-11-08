from fastapi.responses import FileResponse

from app.services.archivo import ArchivoDescargable


def respuesta_video(archivo: ArchivoDescargable, *, inline: bool) -> FileResponse:
    """Envía un vídeo al cliente.

    `inline` lo reproduce en el propio navegador; `attachment` lo descarga como fichero.

    `FileResponse` resuelve además las peticiones `Range` (respondiendo 206 con
    `Content-Range` y anunciando `Accept-Ranges: bytes`), que es lo que permite al
    elemento `<video>` buscar (seek) dentro del fichero sin bajarlo entero.
    """
    return FileResponse(
        archivo.ruta,
        media_type="video/mp4",
        filename=archivo.nombre,
        content_disposition_type="inline" if inline else "attachment",
    )
