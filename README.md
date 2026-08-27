# Comput Digital — Backend

API interna (single-user) para el negocio Comput Digital. Ver `../computdigital-reglas.md` para el spec completo (modelo de datos, endpoints, fases).

## Setup local

```bash
# 1. Entorno virtual (Python 3.12)
py -3.12 -m venv .venv
./.venv/Scripts/activate        # Windows
# source .venv/bin/activate     # Linux/Mac

# 2. Dependencias
pip install -r requirements.txt

# 3. Variables de entorno
cp .env.example .env
# Editar .env con tu DATABASE_URL de Neon, un SECRET_KEY aleatorio,
# y el hash bcrypt de tu contrasena de admin (ver abajo).
```

### Generar el hash de la contraseña de admin

```bash
python -c "from app.core.security import hash_password; print(hash_password('tu-contrasena'))"
```

Copia el resultado en `ADMIN_PASSWORD_HASH` dentro de `.env`.

## Correr el servidor

```bash
uvicorn app.main:app --reload
```

- `GET /health` — chequeo de vida.
- `POST /api/auth/login` — login (form-urlencoded: `username`, `password`) devuelve `{access_token, token_type}`.

## Migraciones (Alembic)

```bash
alembic revision --autogenerate -m "descripcion"
alembic upgrade head
```

La URL de conexión se toma de `DATABASE_URL` en `.env` (no está hardcodeada en `alembic.ini`).

Pendiente de generar contra una base real: la primera migración (tablas `cuenta` y `movimiento_cuenta`). Requiere una `DATABASE_URL` válida en `.env` — correr `alembic revision --autogenerate -m "cuenta y movimiento_cuenta"` y revisar el archivo generado antes de `alembic upgrade head`.

## Seed de las 6 cuentas reales

Una vez migrada la base:

```bash
python -m app.seed
```

Es idempotente — si ya existen no duplica. Crea: Caja (efectivo), Pichincha (cupo_revolvente), Guayaquil/Bolivariano/Pacífico/Fullcarga (fondo_fijo), todas con saldo en 0.00 — los saldos reales se cargan después vía `POST /api/cuentas/{id}/movimientos` o `PATCH /api/cuentas/{id}/cupo`.

## Tests

```bash
pytest
```

Los tests de `cuentas` y `seed` corren contra SQLite en memoria (no requieren Postgres). Los de `auth` tampoco tocan la base.

## Estado

- **Fase 0** — completa: estructura de carpetas, FastAPI + SQLAlchemy 2.0 + Alembic apuntando a Postgres (Neon), auth JWT con un solo admin (sin tabla de usuarios; credenciales vía `.env`).
- **Fase 1** — código completo (modelos `Cuenta`/`MovimientoCuenta`, endpoints, seed, tests). Falta generar y aplicar la migración de Alembic contra una base real (local o Neon) — ver sección de Migraciones arriba.
