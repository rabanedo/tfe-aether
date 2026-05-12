#!/usr/bin/env bash
set -euo pipefail

source ~/miniconda3/etc/profile.d/conda.sh
conda activate /opt/cdse-api/conda_envs/process_server

export PYTHONPATH="/opt/cdse-api:${PYTHONPATH:-}"
export CDSE_BASE_DIR="/opt/cdse-api"
#export CDSE_CONFIG_FILE=/opt/cdse-api/config.txt

exec uvicorn app.api.main:app --host "${CDSE_HOST:-0.0.0.0}" --port "${CDSE_PORT:-8080}"
