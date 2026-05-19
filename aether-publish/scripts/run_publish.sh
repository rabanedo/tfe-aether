#!/usr/bin/env bash
# =============================================================================
# run_publish.sh — Lanzador del script de publicación GeoServer (Nodo 2 Aether)
#
# Se necesita tener instalado en el sistema python3 y el paquete requests:
#   sudo apt install python3-requests   # vía apt
#   pip3 install requests==2.33.1       # vía pip (alternativa)
#
# Uso manual:
#   bash /opt/aether-publish/scripts/run_publish.sh
#   bash /opt/aether-publish/scripts/run_publish.sh --dry-run
#   bash /opt/aether-publish/scripts/run_publish.sh --products s2ndvi s2rgb
# =============================================================================
set -euo pipefail

BASE_DIR="/opt/aether-publish"
PRODUCTS_PATH="${CDSE_GEOSERVER_PRODUCTS_PATH:-/dwh/data}"
ENV_FILE="${BASE_DIR}/.env"
SCRIPT="${BASE_DIR}/app/webmapping/publish.py"

exec python3 "${SCRIPT}" \
    --products-path "${PRODUCTS_PATH}" \
    --env-file      "${ENV_FILE}" \
    "$@"
