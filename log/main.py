import sqlite3
from concurrent import futures
from datetime import datetime
from pathlib import Path

import grpc

from log import log_pb2, log_pb2_grpc


class LogService(log_pb2_grpc.LogServiceServicer):
    def __init__(self, db_path=Path(__file__).with_name("database.db"), address="[::]:50051", max_workers=10):
        self.db_path = db_path
        self._create_table()

        self.server = grpc.server(
            futures.ThreadPoolExecutor(max_workers=max_workers)
        )
        log_pb2_grpc.add_LogServiceServicer_to_server(self, self.server)
        if not self.server.add_insecure_port(address):
            raise RuntimeError(f"No se pudo iniciar el servidor en {address}")
        self.server.start()

    def _create_table(self):
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS LOG (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    fecha TEXT NOT NULL
                )
                """
            )

    def SendData(self, request, context):
        fecha = datetime.now().astimezone().isoformat(timespec="seconds")
        try:
            with sqlite3.connect(self.db_path) as connection:
                connection.execute(
                    "INSERT INTO LOG (url, fecha) VALUES (?, ?)",
                    (request.url, fecha),
                )
        except sqlite3.Error:
            context.abort(
                grpc.StatusCode.INTERNAL,
                "No se pudieron guardar los datos en la base de datos.",
            )

        return log_pb2.DataResponse(
            success=True,
            message="Datos recibidos y guardados correctamente.",
        )

    def wait_for_termination(self):
        self.server.wait_for_termination()


if __name__ == "__main__":
    service = LogService()
    print("Servicio de logs escuchando en el puerto 50051")
    service.wait_for_termination()
