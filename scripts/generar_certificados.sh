#!/usr/bin/env bash
# Genera un certificado autofirmado para HTTPS en certs/.
# No es reconocido por el navegador (el enunciado dice que no es necesario).
# Ejecutar desde la raíz del repositorio.
set -euo pipefail
cd "$(dirname "$0")/.."

mkdir -p certs
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout certs/key.pem \
  -out certs/cert.pem \
  -days 365 \
  -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

echo "Listo: certs/cert.pem y certs/key.pem"
