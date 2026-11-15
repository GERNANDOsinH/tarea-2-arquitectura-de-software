"""Acceso a la base de datos del acortador (Shortener DB).

Lo usan las dos arquitecturas. Cada registro es la 3-tupla <id, hash, long_url>:
  - id:       autoincremental, partiendo en 597652313 (según el enunciado).
  - hash:     el id codificado en base62 (ej. 597652313 -> "eRgfR", el ejemplo del enunciado).
  - long_url: la URL original.

Se usa SQLite: viene con Python y la base queda en un archivo (.db).
"""

import sqlite3
from contextlib import closing
from pathlib import Path

from common import base62

ID_INICIAL = 597652313

_ESQUEMA = """
CREATE TABLE IF NOT EXISTS urls (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    hash     TEXT UNIQUE,
    long_url TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_urls_long_url ON urls(long_url);
"""


class ShortenerDB:
    def __init__(self, ruta: str | Path = "shortener.db") -> None:
        self.ruta = str(ruta)
        self._inicializar()

    def _conectar(self) -> sqlite3.Connection:
        return sqlite3.connect(self.ruta)

    def _inicializar(self) -> None:
        """Crea la tabla y fija el autoincremental para que parta en ID_INICIAL."""
        with closing(self._conectar()) as con, con:
            con.executescript(_ESQUEMA)
            fila = con.execute(
                "SELECT seq FROM sqlite_sequence WHERE name = 'urls'"
            ).fetchone()
            if fila is None:
                # SQLite asigna seq + 1 al próximo registro.
                con.execute(
                    "INSERT INTO sqlite_sequence (name, seq) VALUES ('urls', ?)",
                    (ID_INICIAL - 1,),
                )

    def acortar(self, long_url: str) -> tuple[int, str]:
        """Guarda la URL larga y devuelve (id, hash).

        Si la URL ya estaba registrada, devuelve el hash existente en vez de
        crear uno nuevo.
        """
        with closing(self._conectar()) as con, con:
            existente = con.execute(
                "SELECT id, hash FROM urls WHERE long_url = ? LIMIT 1", (long_url,)
            ).fetchone()
            if existente:
                return existente[0], existente[1]

            # Se inserta primero para obtener el id y luego se calcula el hash.
            # Todo ocurre dentro de la misma transacción.
            cursor = con.execute("INSERT INTO urls (long_url) VALUES (?)", (long_url,))
            nuevo_id = cursor.lastrowid
            hash_ = base62.encode(nuevo_id)
            con.execute("UPDATE urls SET hash = ? WHERE id = ?", (hash_, nuevo_id))
            return nuevo_id, hash_

    def obtener_long_url(self, hash_: str) -> str | None:
        """Devuelve la URL larga asociada al hash, o None si no existe."""
        with closing(self._conectar()) as con:
            fila = con.execute(
                "SELECT long_url FROM urls WHERE hash = ?", (hash_,)
            ).fetchone()
            return fila[0] if fila else None
