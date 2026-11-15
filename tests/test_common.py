from common import base62
from common.db import ID_INICIAL, ShortenerDB
from common.urls import normalizar_url


def test_base62_ida_y_vuelta():
    for n in [0, 1, 61, 62, 12345, ID_INICIAL, 10**12]:
        assert base62.decode(base62.encode(n)) == n


def test_id_inicial_da_hash_de_5_caracteres():
    assert len(base62.encode(ID_INICIAL)) == 5


def test_primer_id_y_autoincremento(tmp_path):
    db = ShortenerDB(tmp_path / "t.db")
    id1, h1 = db.acortar("https://usm.cl/a")
    id2, h2 = db.acortar("https://usm.cl/b")
    assert id1 == ID_INICIAL
    assert id2 == ID_INICIAL + 1
    assert h1 == base62.encode(id1) and h2 == base62.encode(id2)


def test_misma_url_reutiliza_hash(tmp_path):
    db = ShortenerDB(tmp_path / "t.db")
    assert db.acortar("https://usm.cl/a") == db.acortar("https://usm.cl/a")


def test_busqueda_y_persistencia(tmp_path):
    ruta = tmp_path / "t.db"
    _, h = ShortenerDB(ruta).acortar("https://usm.cl/a")
    # Abrir de nuevo la base: los datos y el contador siguen ahí.
    db = ShortenerDB(ruta)
    assert db.obtener_long_url(h) == "https://usm.cl/a"
    assert db.obtener_long_url("noexiste") is None
    assert db.acortar("https://usm.cl/b")[0] == ID_INICIAL + 1


def test_normalizar_url():
    assert normalizar_url("usm.cl/informatica") == "https://usm.cl/informatica"
    assert normalizar_url("http://usm.cl") == "http://usm.cl"
    assert normalizar_url("ftp://usm.cl") is None
    assert normalizar_url("hola") is None
    assert normalizar_url("") is None
