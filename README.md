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