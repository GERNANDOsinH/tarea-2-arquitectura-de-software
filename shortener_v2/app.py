"""Shortener v2 (Arquitectura 2).

- POST /shorten   recibe {"long_url": "..."} y devuelve la URL corta.
- GET  /{hash}    redirige con HTTP 301 (permanente) para que el navegador
                  cachee el destino.

Tácticas arquitectónicas implementadas en LiteStar:
  1. Controlar arribo de eventos: RateLimitConfig (ej. 10 peticiones por minuto).
  2. Mantener múltiples copias de datos: ResponseCacheConfig + cache en GET.

Configuración por variables de entorno:
  SHORTENER_DB    ruta del archivo SQLite         (default: shortener_v2.db)
  BASE_URL        prefijo de las URLs cortas      (default: https://localhost:8001)
  RATE_LIMIT      peticiones máximas por minuto   (default: 10)
  CACHE_TTL       segundos de vida en caché       (default: 60)
"""

import os
from dataclasses import dataclass

from litestar import Litestar, get, post
from litestar.config.response_cache import ResponseCacheConfig
from litestar.exceptions import HTTPException, NotFoundException
from litestar.middleware.rate_limit import RateLimitConfig
from litestar.params import FromPath, JSONBody
from litestar.response import Redirect

from common.db import ShortenerDB
from common.urls import normalizar_url

BASE_URL = os.getenv("BASE_URL", "https://localhost:8001").rstrip("/")
RATE_LIMIT_MAX = int(os.getenv("RATE_LIMIT", "10"))
CACHE_TTL = int(os.getenv("CACHE_TTL", "60"))

db = ShortenerDB(os.getenv("SHORTENER_DB", "shortener_v2.db"))


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


# cache=CACHE_TTL guarda la respuesta HTTP 301 en el caché de LiteStar
# evitando consultas repetidas a SQLite para el mismo hash.
@get("/{hash_:str}", cache=CACHE_TTL)
async def redirigir(hash_: FromPath[str]) -> Redirect:
    long_url = db.obtener_long_url(hash_)
    if long_url is None:
        raise NotFoundException(detail="URL corta no encontrada")

    return Redirect(
        path=long_url,
        status_code=301,
    )


# Táctica 1: Controlar arribo de eventos (Rate Limiting)
rate_limit_config = RateLimitConfig(
    rate_limit=("minute", RATE_LIMIT_MAX),
    exclude=["/schema"],
)

# Táctica 2: Mantener múltiples copias de datos (Caching en servidor)
response_cache_config = ResponseCacheConfig(
    default_expiration=CACHE_TTL,
)

app = Litestar(
    route_handlers=[acortar, redirigir],
    middleware=[rate_limit_config.middleware],
    response_cache_config=response_cache_config,
)