from fastapi import FastAPI

from app.routers import auth, cuentas

app = FastAPI(title="Comput Digital API")

app.include_router(auth.router)
app.include_router(cuentas.router)


@app.get("/health")
def health():
    return {"status": "ok"}
