from fastapi import FastAPI

from app.routers import arqueo, auth, conteo_monedas, cuentas, servicios

app = FastAPI(title="Comput Digital API")

app.include_router(auth.router)
app.include_router(cuentas.router)
app.include_router(servicios.router)
app.include_router(arqueo.router)
app.include_router(conteo_monedas.router)


@app.get("/health")
def health():
    return {"status": "ok"}
