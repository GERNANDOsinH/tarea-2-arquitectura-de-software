"""Pruebas de integración: Shortener v1 + servicio Log real (log/main.py)."""

import importlib
import socket
import sqlite3

import pytest
from litestar.testing import TestClient

from log.main import LogService


def _puerto_libre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def servicio_log(tmp_path):
    puerto = _puerto_libre()
    db_log = tmp_path / "log_test.db"
    servicio = LogService(db_path=db_log, address=f"127.0.0.1:{puerto}")
    yield db_log, f"127.0.0.1:{puerto}"
    servicio.server.stop(None)


def _cliente(monkeypatch, tmp_path, log_addr):
    monkeypatch.setenv("SHORTENER_DB", str(tmp_path / "v1.db"))
    monkeypatch.setenv("LOG_GRPC_ADDR", log_addr)
    from shortener_v1 import app as modulo_app, log_client

    importlib.reload(log_client)
    importlib.reload(modulo_app)
    return TestClient(app=modulo_app.app)


def test_post_y_redireccion_302_queda_en_el_log(monkeypatch, tmp_path, servicio_log):
    db_log, addr = servicio_log
    with _cliente(monkeypatch, tmp_path, addr) as cliente:
        r = cliente.post("/shorten", json={"long_url": "usm.cl/informatica/postgrado"})
        assert r.status_code == 201
        datos = r.json()
        assert datos["id"] == 597652313
        assert datos["hash"] == "eRgfR"

        r = cliente.get("/eRgfR", follow_redirects=False)
        assert r.status_code == 302
        assert r.headers["location"] == "https://usm.cl/informatica/postgrado"

    with sqlite3.connect(db_log) as con:
        filas = con.execute("SELECT url, fecha FROM LOG").fetchall()
    assert len(filas) == 1
    assert filas[0][0] == datos["short_url"]
    assert filas[0][1]  # el Log guardó la fecha


def test_redirige_aunque_el_log_este_caido(monkeypatch, tmp_path):
    with _cliente(monkeypatch, tmp_path, "127.0.0.1:1") as cliente:
        h = cliente.post("/shorten", json={"long_url": "https://usm.cl"}).json()["hash"]
        assert cliente.get(f"/{h}", follow_redirects=False).status_code == 302


def test_hash_inexistente_y_url_invalida(monkeypatch, tmp_path):
    with _cliente(monkeypatch, tmp_path, "127.0.0.1:1") as cliente:
        assert cliente.get("/noexiste", follow_redirects=False).status_code == 404
        assert cliente.post("/shorten", json={"long_url": "hola"}).status_code == 400
