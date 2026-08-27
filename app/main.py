from fastapi import FastAPI

from app.routers import (
    arqueo,
    auth,
    comisiones,
    conteo_monedas,
    cuentas,
    directorio,
    inventario,
    servicios,
    ventas,
)

app = FastAPI(title="Comput Digital API")

app.include_router(auth.router)
app.include_router(cuentas.router)
app.include_router(servicios.router)
app.include_router(arqueo.router)
app.include_router(conteo_monedas.router)
app.include_router(ventas.router)
app.include_router(comisiones.router)
app.include_router(directorio.router)
app.include_router(inventario.router)


@app.get("/health")
def health():
    return {"status": "ok"}
