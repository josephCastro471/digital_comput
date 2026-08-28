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
- Los 2 proveedores de comisión con sus % reales: Payphone (`comision_pct=5`, `iva_pct=15`) y Deuna (`comision_pct=4`, `iva_pct=15`), ambos con `aplica_iva=true`. No hay endpoint `POST` para proveedores (regla dura: la config va en tabla, no en código) — si la tarifa cambia, se ajusta vía `PATCH /api/comisiones/proveedores/{id}`.

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

## Directorio de códigos/notas (Fase 6)

CRUD simple (`Directorio`), tipo `empresa` o `cliente`, con campos opcionales `codigo`/`red`/`cedula_cuenta`/`nota`.

- `GET /api/directorio?buscar=` — busca (case-insensitive) en `nombre`, `codigo`, `red`, `cedula_cuenta` y `nota`.
- `POST /api/directorio`, `PATCH /api/directorio/{id}` (el PATCH permite limpiar un campo enviándolo como `null`), `DELETE /api/directorio/{id}`.

## Inventario de accesorios (Fase 7)

- `GET /api/inventario`, `POST /api/inventario` (acepta `stock_actual` inicial, default 0).
- `PATCH /api/inventario/{id}` — solo `nombre`/`costo`/`precio_venta`. El stock **no** se edita por PATCH, solo vía movimientos (mismo principio que `saldo_actual` en cuentas).
- `POST /api/inventario/{id}/movimiento` — `tipo` es `"entrada"` o `"salida"` (a diferencia de los demás módulos, el modelo lo define como `str` libre, no un enum — ver `computdigital-reglas.md`); `salida` rechaza con 400 si `cantidad` supera el `stock_actual`. Devuelve el movimiento creado (no el accesorio).

## Dashboard / reportes (Fase 8)

Sin tablas nuevas — agrega datos de los módulos existentes. Ambos endpoints devuelven `ventas` (cantidad/total), `comisiones` (cantidad/total_comision/total_iva_sobre_comision/total_valor_cobrado), `arqueos` (lista, filtrados por `fecha_apertura` en el rango) y `cuentas` (snapshot del saldo **actual**, no reconstruye saldo histórico por fecha).

- `GET /api/dashboard/resumen?fecha=` — resumen de un día.
- `GET /api/dashboard/rango?desde=&hasta=` — mismo resumen agregado sobre un rango; 400 si `hasta < desde`.

## Tests

```bash
pytest
```

Los tests de `cuentas`, `servicios`, `arqueo`, `conteo-monedas`, `ventas`, `comisiones`, `directorio`, `inventario`, `dashboard` y `seed` corren contra SQLite en memoria (no requieren Postgres). Los de `auth` tampoco tocan la base.

## Estado

- **Fase 0** — completa: estructura de carpetas, FastAPI + SQLAlchemy 2.0 + Alembic apuntando a Postgres, auth JWT con un solo admin (sin tabla de usuarios; credenciales vía `.env`).
- **Fase 1** — completa y migrada: modelos `Cuenta`/`MovimientoCuenta`, endpoints, seed de las 6 cuentas reales.
- **Fase 2** — completa y migrada: catálogo de servicios (`Servicio`/`EscalonPrecio`), endpoints. La UI de alta rápida queda pendiente para cuando arranque `computdigital-frontend/`.
- **Fase 3** — completa y migrada: `ArqueoCaja`/`ArqueoDetalle` (por turno, un abierto a la vez) y `ConteoMonedas` (independiente, no toca cuentas).
- **Fase 4** — completa y migrada: `Venta`/`VentaItem`, precio automático según `tipo_precio`, depósito automático en cuenta cuando se especifica `cuenta_id`.
- **Fase 5** — completa y migrada: `ProveedorComision`/`TransaccionComision`, calculadora de comisiones. La fórmula es de "gross-up": `valor_recibir` es el neto que el negocio se debe quedar, `valor_cobrado` se calcula para que, tras descontar comisión + IVA sobre la comisión, quede exacto ese neto. Payphone (5% + IVA 15%) y Deuna (4% + IVA 15%) sembrados con sus % reales.
- **Fase 6** — completa y migrada: `Directorio` de códigos/notas con búsqueda.
- **Fase 7** — completa y migrada: `Accesorio`/`MovimientoInventario`, stock protegido contra salidas mayores al disponible.
- **Fase 8** — completa (sin migración, no crea tablas): dashboard con resumen diario y por rango.
- **Fase 9** — CI con GitHub Actions, `render.yaml`, y ya desplegado en producción: backend en Render, frontend en Vercel, base en Neon.

## Cuadre de fondos fijos (post-deploy)

Los 4 fondos fijos (Guayaquil, Bolivariano, Pacífico, Fullcarga) representan efectivo entregado a clientes por retiros vía el banco correspondiente — Joseph verifica el saldo real de la cuenta bancaria a mano, no registra un movimiento por cada retiro. Un solo endpoint, restringido a `tipo=fondo_fijo`:

- `POST /api/cuentas/{id}/cuadre` — `{valor_actual}`: calcula `recaudado = valor_inicial (lo guardado desde el último cuadre) - valor_actual`. `valor_actual` es lo que Joseph decide que queda en la cuenta ahora mismo (haya retirado todo, una parte, o nada — no es necesariamente el saldo bancario literal si retiró solo una parte). Ese valor se guarda tanto en `saldo_actual` como en `saldo_inicial_dia`, así que pasa a ser el `valor_inicial` del próximo cuadre automáticamente — no hay pasos separados de abrir/cerrar día. Devuelve `{recaudado, valor_inicial, valor_actual, cuenta}`.

  Ejemplo real: Fullcarga arranca con 290 de valor inicial; el banco marca 275.35 pero Joseph solo retira 10, así que escribe `valor_actual=280` → recaudado 10, y 280 queda como el valor inicial del próximo cuadre. Bolivariano arranca con 323.54, retira todo y escribe `valor_actual=92.34` → recaudado 231.20.

Reutiliza `MovimientoCuenta` para el historial — no se agregó ninguna tabla ni columna nueva.

## CI

`.github/workflows/tests.yml` corre `pytest` en cada push/PR a `main` (Python 3.12, con variables de entorno dummy solo para que `Settings()` pueda instanciarse — los tests usan SQLite en memoria, nunca tocan una base real).

## Deploy a producción (Render + Neon)

1. En Neon, crear (o usar) la base de datos y copiar la connection string. Armar el `DATABASE_URL` con el prefijo de SQLAlchemy: `postgresql+psycopg://usuario:password@ep-xxx.neon.tech/nombre_db?sslmode=require`.
2. En Render: **New > Blueprint**, conectar este repo — Render lee `render.yaml` y crea el servicio automáticamente.
3. Completar las variables de entorno marcadas `sync: false` en el dashboard de Render (no van en `render.yaml` por ser secretas):
   - `DATABASE_URL` — la de Neon del paso 1.
   - `SECRET_KEY` — una cadena aleatoria (no reutilizar la de desarrollo local).
   - `ADMIN_USERNAME` / `ADMIN_PASSWORD_HASH` — ver "Generar el hash de la contraseña de admin" arriba.
   - `CORS_ORIGINS` — la URL del frontend en Vercel una vez desplegado (ej: `https://digital-comput-front.vercel.app`). Sin esto, el navegador bloquea las llamadas del frontend por CORS.
4. El build de Render corre `pip install -r requirements.txt && alembic upgrade head && python -m app.seed` — migra el schema y siembra las 6 cuentas reales + Payphone/Deuna automáticamente en cada deploy (idempotente, no duplica).
5. `healthCheckPath: /health` — Render lo usa para saber si el servicio arrancó bien.
