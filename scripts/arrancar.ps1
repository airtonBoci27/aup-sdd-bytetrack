Param(
    [int]$Puerto = 8000,
    [switch]$SoloVerificar
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

Write-Host "== ByteTrack v1.0 · Despliegue Local Reproducible (Fase de Transición) ==" -ForegroundColor Cyan

if (-not (Test-Path ".env")) {
    Write-Error "No existe el archivo .env. Copie .env.example a .env y configure BYTETRACK_JWT_SECRET, BYTETRACK_RECEPCIONISTA_CLAVE y BYTETRACK_TECNICO_CLAVE (Principio VI)."
    exit 1
}

Write-Host "[1/4] Sincronizando entorno Python 3.12 con uv..." -ForegroundColor Yellow
uv sync --frozen

Write-Host "[2/4] Cargando datos iniciales de forma idempotente (app.seed)..." -ForegroundColor Yellow
uv run python -m app.seed

Write-Host "[3/4] Ejecutando pruebas de humo y rendimiento (RNF-03)..." -ForegroundColor Yellow
uv run pytest tests/test_transicion_humo_rnf03.py -q

if ($SoloVerificar) {
    Write-Host "[OK] Verificación de Transición completada correctamente." -ForegroundColor Green
    exit 0
}

Write-Host "[4/4] Iniciando servidor ByteTrack en http://127.0.0.1:$Puerto ..." -ForegroundColor Green
uv run uvicorn app.main:app --host 127.0.0.1 --port $Puerto
