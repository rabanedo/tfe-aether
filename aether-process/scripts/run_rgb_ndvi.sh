#!/bin/bash
set -euo pipefail
source /opt/miniconda3/etc/profile.d/conda.sh
conda activate /opt/miniconda3/envs/cdse-api
exec python3 /opt/cdse-api/app/services/rgb_ndvi.py "$@"