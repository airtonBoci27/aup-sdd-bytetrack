#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
PUERTO="${1:-8000}"

echo "== ByteTrack v1.0 · Despliegue Local Reproducible (Fase de Transición) =="

if [ ! -f ".env" ]; then
  echo "Error: no existe .env. Copie .env.example a .env y defina las variables secretas (Principio VI)." >&2
  exit 1
fi

echo "[1/4] Sincronizando entorno Python 3.12 con uv..."
uv sync --frozen

echo "[2/4] Cargando datos iniciales idempotentes (app.seed)..."
uv run python -m app.seed

echo "[3/4] Ejecutando pruebas de humo y rendimiento (RNF-03)..."
uv run pytest tests/test_transicion_humo_rnf03.py -q

echo "[4/4] Iniciando servidor ByteTrack en http://127.0.0.1:${PUERTO} ..."
exec uv run uvicorn app.main:app --host 127.0.0.1 --port "${PUERTO}"
