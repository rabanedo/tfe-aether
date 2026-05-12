#!/usr/bin/env bash
set -euo pipefail
BASE_URL="${BASE_URL:-http://127.0.0.1:8080}"
PAYLOAD="${PAYLOAD:-{}}"
curl -sS -X POST "$BASE_URL/api/v1/pipeline/run" -H 'Content-Type: application/json' -d "$PAYLOAD"
