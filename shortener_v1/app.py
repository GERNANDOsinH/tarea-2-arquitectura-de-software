"""Shortener v1 (Arquitectura 1).

- POST /shorten   recibe {"long_url": "..."} y devuelve la URL corta.
- GET  /{hash}    redirige con HTTP 302 (temporal) y envía un evento "url hit"
                  al servicio Log (carpeta log/) por gRPC.

El 302 evita que el navegador guarde la redirección en caché: así cada visita
pasa por este servicio y queda registrada en el Log.

Configuración por variables de entorno:
  SHORTENER_DB    ruta del archivo SQLite         (default: shortener_v1.db)
  BASE_URL        prefijo de las URLs cortas      (default: https://localhost:8000)
  LOG_GRPC_ADDR   dirección del servicio Log      (default: localhost:50051)
"""

import logging
import os
from dataclasses import dataclass

from litestar import Litestar, get, post
from litestar.background_tasks import BackgroundTask
from litestar.exceptions import HTTPException, NotFoundException
from litestar.params import FromPath, JSONBody
from litestar.response import Redirect

from shortener_v1.log_client import enviar_hit
from common.db import ShortenerDB
from common.urls import normalizar_url

logger = logging.getLogger("shortener_v1")

BASE_URL = os.getenv("BASE_URL", "https://localhost:8000").rstrip("/")
db = ShortenerDB(os.getenv("SHORTENER_DB", "shortener_v1.db"))


@dataclass
class AcortarRequest:
    long_url: str


@dataclass
class AcortarResponse:
    id: int
    hash: str
    short_url: str
    long_url: str


@post("/shorten")
async def acortar(data: JSONBody[AcortarRequest]) -> AcortarResponse:
    long_url = normalizar_url(data.long_url)
    if long_url is None:
        raise HTTPException(status_code=400, detail="URL inválida")
    id_, hash_ = db.acortar(long_url)
    return AcortarResponse(
        id=id_, hash=hash_, short_url=f"{BASE_URL}/{hash_}", long_url=long_url
    )


@get("/{hash_:str}")
async def redirigir(hash_: FromPath[str]) -> Redirect:
    long_url = db.obtener_long_url(hash_)
    if long_url is None:
        raise NotFoundException(detail="URL corta no encontrada")

    short_url = f"{BASE_URL}/{hash_}"

    # El hit (URL visitada) se envía en una tarea de fondo, después de responder:
    # si el Log está caído o lento, el usuario igual es redirigido sin esperar.
    # El servicio Log guarda la fecha y hora en que recibe el evento.
    return Redirect(
        path=long_url,
        status_code=302,
        background=BackgroundTask(enviar_hit, short_url),
    )


app = Litestar(route_handlers=[acortar, redirigir])
