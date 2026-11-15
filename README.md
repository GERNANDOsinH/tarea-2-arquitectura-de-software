# tarea-2-arquitectura-de-software

## Servicio gRPC de logs

Desde la raíz del repositorio, crea el entorno e instala las dependencias:

```bash
python3 -m venv log/.venv
log/.venv/bin/python -m pip install -r log/requirements.txt
```

Para compilar `log/log.proto` y generar los mensajes y stubs del servicio:

```bash
log/.venv/bin/python -m grpc_tools.protoc \
  -I . \
  --python_out=. \
  --grpc_python_out=. \
  log/log.proto
```

Para iniciar el servicio:

```bash
log/.venv/bin/python -m log.main
```

## Shortener v1 (Arquitectura 1)

Servicio HTTP en LiteStar que acorta URLs y, al visitar una URL corta, responde
con una redirección **302** y envía el evento "url hit" al servicio de logs por gRPC.

### Instalación

Desde la raíz del repositorio:

```bash
python3 -m venv shortener_v1/.venv
shortener_v1/.venv/bin/python -m pip install -r shortener_v1/requirements.txt
./scripts/generar_certificados.sh   # crea certs/cert.pem y certs/key.pem
```

### Ejecución

Primero levantar el servicio de logs (ver sección anterior) y luego, en otra terminal:

```bash
shortener_v1/.venv/bin/python -m uvicorn shortener_v1.app:app --port 8000 \
  --ssl-keyfile certs/key.pem --ssl-certfile certs/cert.pem
```

### Prueba rápida

```bash
# Acortar una URL
curl -k -X POST https://localhost:8000/shorten \
  -H "Content-Type: application/json" \
  -d '{"long_url": "usm.cl/informatica/postulaciones-a-postgrado/2025/magiste-en-ingenieria-informatica/"}'
# -> {"id":597652313,"hash":"eRgfR","short_url":"https://localhost:8000/eRgfR",...}

# Visitar la URL corta (muestra el 302 sin seguirlo)
curl -k -i https://localhost:8000/eRgfR
```

`-k` es necesario porque el certificado es autofirmado.

Variables de entorno opcionales:

| Variable | Default | Uso |
|---|---|---|
| `SHORTENER_DB` | `shortener_v1.db` | Archivo SQLite de la Shortener DB |
| `BASE_URL` | `https://localhost:8000` | Prefijo de las URLs cortas |
| `LOG_GRPC_ADDR` | `localhost:50051` | Dirección del servicio de logs |

### Pruebas

```bash
shortener_v1/.venv/bin/python -m pip install -r log/requirements.txt
shortener_v1/.venv/bin/python -m pytest -q
```

Las pruebas levantan el servicio de logs real (`log/main.py`) con una base temporal.

### Consideraciones de implementación

- **Base común (`common/`):** la usan ambas arquitecturas. `db.py` maneja la Shortener DB
  en SQLite con la 3-tupla `<id, hash, long_url>`; `base62.py` codifica los ids;
  `urls.py` valida las URLs recibidas.
- **Ids y hashes:** el id es autoincremental y parte en 597652313. El hash es el id en
  base62 (alfabeto `0-9A-Za-z`, compatible con `pybase62`); el primer id produce `eRgfR`,
  igual que el ejemplo del enunciado. Como cada id es único, los hashes no colisionan.
- **URLs repetidas:** si se acorta una URL ya registrada, se devuelve el hash existente.
- **Validación:** se aceptan URLs `http`/`https`; si llegan sin esquema se les agrega
  `https://`. URLs inválidas responden 400 y hashes inexistentes responden 404.
- **Envío del hit:** se envía la URL corta visitada por gRPC (`SendData`) en una tarea de
  fondo, después de responder el 302. Si el servicio de logs está caído o lento
  (timeout de 2 s), el usuario igual es redirigido y solo se registra una advertencia.
  Se reutiliza un único canal gRPC.
- **HTTPS:** certificado autofirmado para `localhost` generado con OpenSSL. El canal gRPC
  interno entre el shortener y el servicio de logs es sin TLS (mismo nodo).
