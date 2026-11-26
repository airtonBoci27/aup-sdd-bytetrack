# Plan de Despliegue Local y Operación — ByteTrack v1.0

**Fase AUP**: Transición (`T1`) · **Especificación**: `specs/004-transicion-despliegue/`

## 1. Requisitos del Entorno

- **Sistema Operativo**: Windows 10/11 (64 bits), Linux o macOS.
- **Runtime y Gestor**: Python `3.12.x` y `uv` (`>= 0.5`).
- **Recursos mínimos**: 2 núcleos CPU, 4 GB RAM, 200 MB de almacenamiento local para SQLite en modo `WAL`.
- **Navegador cliente**: Chrome, Edge o Firefox actualizado (soporte nativo de ES Modules).

## 2. Configuración de Variables de Entorno (Principio VI)

1. Copiar la plantilla sin secretos en la raíz del repositorio:
   ```powershell
   Copy-Item .env.example .env
   ```
2. Generar una clave de firma JWT criptográficamente segura (`>= 32` caracteres) y definir las contraseñas iniciales en `.env` (archivo ignorado por Git):
   ```powershell
   uv run python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```
   Variables obligatorias en `.env`:
   - `BYTETRACK_JWT_SECRET`: clave secreta HS256 (mínimo 32 caracteres).
   - `BYTETRACK_RECEPCIONISTA_CLAVE`: contraseña inicial del usuario `recepcion`.
   - `BYTETRACK_TECNICO_CLAVE`: contraseña inicial del usuario `tecnico`.

## 3. Puesta en Marcha Reproducible

### En Windows (PowerShell)
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\arrancar.ps1
```

### En Linux / macOS (Bash)
```bash
chmod +x ./scripts/arrancar.sh
./scripts/arrancar.sh
```

El script ejecuta en orden:
1. Validación de existencia de `.env` y sincronización exacta desde `uv.lock` (`uv sync --frozen`).
2. Inicialización idempotente de tablas, usuarios (`scrypt`), técnicos, repuestos y datos base (`uv run python -m app.seed`).
3. Ejecución de pruebas de humo (`uv run pytest tests/test_transicion_humo_rnf03.py -q`).
4. Arranque del servidor ASGI Uvicorn en `http://127.0.0.1:8000` (interfaz web en `/` y documentación OpenAPI en `/docs`).

## 4. Respaldo y Restauración (SQLite WAL)

Dado que SQLite opera con `PRAGMA journal_mode=WAL`, realizar respaldos consistentes en caliente con la API nativa de SQLite:

```powershell
uv run python -c "import sqlite3; src=sqlite3.connect('bytetrack.db'); dst=sqlite3.connect('backup_bytetrack.db'); src.backup(dst); dst.close(); src.close()"
```

Para **reversión (rollback)** ante una actualización fallida: detener Uvicorn, eliminar `bytetrack.db`, `bytetrack.db-wal` y `bytetrack.db-shm`, restaurar `backup_bytetrack.db` como `bytetrack.db` y reiniciar el servicio.

## 5. Hoja de Ruta hacia la Arquitectura Objetivo en AWS (`caso.md` §3.5)

La arquitectura en capas con SQLAlchemy 2.x permite migrar del despliegue local del taller a AWS (`sa-east-1`) sin reescribir reglas de negocio:
1. Sustituir `sqlite:///` en `app/database.py` por `postgresql+psycopg://` apuntando a **Amazon RDS PostgreSQL Multi-AZ** y cambiar `BEGIN IMMEDIATE` por `SELECT ... FOR UPDATE` en `orden_repository` y `repuesto_repository`.
2. Empaquetar `app/` en contenedor Docker para **AWS ECS Fargate** detrás de un Application Load Balancer con TLS.
3. Publicar `app/web/` en **Amazon S3 + CloudFront + AWS WAF** e inyectar secretos desde **AWS Secrets Manager**.
