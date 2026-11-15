"""Cliente gRPC hacia el servicio Log (carpeta log/).

Usa el contrato definido en log/log.proto: rpc SendData(DataRequest{url}).
"""

import logging
import os

import grpc

from log import log_pb2, log_pb2_grpc

logger = logging.getLogger("shortener_v1.log_client")

LOG_GRPC_ADDR = os.getenv("LOG_GRPC_ADDR", "localhost:50051")
TIMEOUT_SEGUNDOS = 2.0

_canal: grpc.aio.Channel | None = None
_stub: log_pb2_grpc.LogServiceStub | None = None


def _obtener_stub() -> log_pb2_grpc.LogServiceStub:
    """Reutiliza un único canal gRPC en vez de abrir uno por cada visita."""
    global _canal, _stub
    if _stub is None:
        _canal = grpc.aio.insecure_channel(LOG_GRPC_ADDR)
        _stub = log_pb2_grpc.LogServiceStub(_canal)
    return _stub


async def enviar_hit(url: str) -> bool:
    """Envía un evento "url hit" al Log. Nunca lanza excepciones.

    El servicio Log registra la fecha y hora en que recibe el evento.
    Devuelve True si el Log confirmó el registro.
    """
    try:
        respuesta = await _obtener_stub().SendData(
            log_pb2.DataRequest(url=url), timeout=TIMEOUT_SEGUNDOS
        )
        return respuesta.success
    except grpc.aio.AioRpcError as error:
        logger.warning("No se pudo registrar el hit en el Log: %s", error.code())
        return False
