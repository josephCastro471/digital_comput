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

Migraciones aplicadas hasta ahora: `cuenta`/`movimiento_cuenta` (Fase 1) y `servicio`/`escalon_precio` (Fase 2).

## Seed de las 6 cuentas reales

Una vez migrada la base:

```bash
python -m app.seed
```

Es idempotente — si ya existen no duplica. Crea: Caja (efectivo), Pichincha (cupo_revolvente), Guayaquil/Bolivariano/Pacífico/Fullcarga (fondo_fijo), todas con saldo en 0.00 — los saldos reales se cargan después vía `POST /api/cuentas/{id}/movimientos` o `PATCH /api/cuentas/{id}/cupo`.

## Catálogo de servicios (Fase 2)

`POST /api/servicios` acepta 3 tipos de precio vía `tipo_precio`:

- `fijo` — requiere `precio_base` (> 0), sin escalones.
- `variable` — sin `precio_base` ni escalones (el precio se define en cada venta, Fase 4).
- `escalonado` — sin `precio_base`, requiere `escalones: [{cantidad_desde, cantidad_hasta, precio_unitario}]` ordenados sin solaparse; el último escalón puede dejar `cantidad_hasta: null` (abierto).

No hay seed de servicios — regla dura: el catálogo lo carga Joseph directo en el sistema.

## Tests

```bash
pytest
```

Los tests de `cuentas`, `servicios` y `seed` corren contra SQLite en memoria (no requieren Postgres). Los de `auth` tampoco tocan la base.

## Estado

- **Fase 0** — completa: estructura de carpetas, FastAPI + SQLAlchemy 2.0 + Alembic apuntando a Postgres, auth JWT con un solo admin (sin tabla de usuarios; credenciales vía `.env`).
- **Fase 1** — completa y migrada: modelos `Cuenta`/`MovimientoCuenta`, endpoints, seed de las 6 cuentas reales.
- **Fase 2** — completa y migrada: catálogo de servicios (`Servicio`/`EscalonPrecio`), endpoints. La UI de alta rápida queda pendiente para cuando arranque `computdigital-frontend/`.
