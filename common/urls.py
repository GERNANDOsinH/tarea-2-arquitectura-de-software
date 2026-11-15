"""Validación de URLs que llegan al POST."""

from urllib.parse import urlparse


def normalizar_url(url: str) -> str | None:
    """Devuelve la URL lista para guardar, o None si no es válida.

    Si viene sin esquema (ej. "usm.cl/informatica"), se le agrega https://.
    """
    url = (url or "").strip()
    if not url:
        return None
    if "://" not in url:
        url = "https://" + url
    partes = urlparse(url)
    if partes.scheme not in ("http", "https") or not partes.netloc or "." not in partes.netloc:
        return None
    return url
