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

Es idempotente — si ya existen no duplica. Crea:
- Las 6 cuentas reales: Caja (efectivo), Pichincha (cupo_revolvente), Guayaquil/Bolivariano/Pacífico/Fullcarga (fondo_fijo), todas con saldo en 0.00 — los saldos reales se cargan después vía `POST /api/cuentas/{id}/movimientos` o `PATCH /api/cuentas/{id}/cupo`.
- Los 2 proveedores de comisión (Payphone, Deuna) con `comision_pct`/`iva_pct` en 0 — no hay endpoint `POST` para proveedores (regla dura: la config va en tabla, no en código), así que se siembran acá y se configuran los % reales después vía `PATCH /api/comisiones/proveedores/{id}`.

## Catálogo de servicios (Fase 2)

`POST /api/servicios` acepta 3 tipos de precio vía `tipo_precio`:

- `fijo` — requiere `precio_base` (> 0), sin escalones.
- `variable` — sin `precio_base` ni escalones (el precio se define en cada venta, Fase 4).
- `escalonado` — sin `precio_base`, requiere `escalones: [{cantidad_desde, cantidad_hasta, precio_unitario}]` ordenados sin solaparse; el último escalón puede dejar `cantidad_hasta: null` (abierto).

No hay seed de servicios — regla dura: el catálogo lo carga Joseph directo en el sistema.

## Arqueo de caja y conteo de monedas (Fase 3)

- `POST /api/arqueo/abrir` — abre un turno (`saldo_apertura` opcional, default 40.00). Falla con 409 si ya hay un turno `abierto` (regla dura: solo uno a la vez).
- `POST /api/arqueo/{id}/cerrar` — recibe `detalles: [{denominacion, cantidad}]` (conteo físico del efectivo), calcula `saldo_cierre` y `ganancia_neta = saldo_cierre - saldo_apertura`.
- `GET /api/arqueo?estado=&fecha=` y `GET /api/arqueo/{id}`.
- `POST /api/conteo-monedas` — calculadora de apoyo para conteo de monedas de terceros (`denominaciones: {"0.05": 50, ...}`, calcula `total`). **Nunca** crea `movimiento_cuenta` — no afecta saldos.
- `GET /api/conteo-monedas?fecha=`.

## Ventas (Fase 4)

`POST /api/ventas` conecta el catálogo de servicios con el núcleo de cuentas:

- `items: [{servicio_id, cantidad, precio_unitario?}]` — `precio_unitario` es obligatorio solo para servicios `variable`; para `fijo` se toma `precio_base` y para `escalonado` se busca el tramo cuyo rango contiene la `cantidad`.
- `cuenta_id` opcional — si se envía, la venta genera automáticamente un `movimiento_cuenta` tipo `deposito` por el `total` (con `referencia_tipo="venta"`), reutilizando la misma lógica de aplicación de saldo que `POST /api/cuentas/{id}/movimientos` (función `aplicar_movimiento` compartida entre ambos routers). Sin `cuenta_id`, la venta no toca ningún saldo.
- `GET /api/ventas?fecha=`, `GET /api/ventas/{id}`.

## Comisiones digitales (Fase 5)

- `GET /api/comisiones/proveedores`, `PATCH /api/comisiones/proveedores/{id}` — configura `comision_pct`, `aplica_iva`, `iva_pct` por proveedor (Payphone, Deuna). Sin `POST`: los proveedores se siembran con `python -m app.seed`, no se crean por API.
- `POST /api/comisiones/calcular` — calculadora pura (no persiste): dado `proveedor_id` + `valor_recibir`, devuelve `comision`, `iva_sobre_comision` y `valor_cobrado`.
- `POST /api/comisiones/transacciones` — igual cálculo pero persiste un `TransaccionComision`.
- `GET /api/comisiones/transacciones?fecha=`.

## Tests

```bash
pytest
```

Los tests de `cuentas`, `servicios`, `arqueo`, `conteo-monedas`, `ventas`, `comisiones` y `seed` corren contra SQLite en memoria (no requieren Postgres). Los de `auth` tampoco tocan la base.

## Estado

- **Fase 0** — completa: estructura de carpetas, FastAPI + SQLAlchemy 2.0 + Alembic apuntando a Postgres, auth JWT con un solo admin (sin tabla de usuarios; credenciales vía `.env`).
- **Fase 1** — completa y migrada: modelos `Cuenta`/`MovimientoCuenta`, endpoints, seed de las 6 cuentas reales.
- **Fase 2** — completa y migrada: catálogo de servicios (`Servicio`/`EscalonPrecio`), endpoints. La UI de alta rápida queda pendiente para cuando arranque `computdigital-frontend/`.
- **Fase 3** — completa y migrada: `ArqueoCaja`/`ArqueoDetalle` (por turno, un abierto a la vez) y `ConteoMonedas` (independiente, no toca cuentas).
- **Fase 4** — completa y migrada: `Venta`/`VentaItem`, precio automático según `tipo_precio`, depósito automático en cuenta cuando se especifica `cuenta_id`.
- **Fase 5** — completa y migrada: `ProveedorComision`/`TransaccionComision`, calculadora de comisiones, Payphone/Deuna sembrados con 0% (configurar los % reales vía PATCH).
