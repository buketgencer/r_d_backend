from fastapi import FastAPI
from .api.v1.endpoints import router as v1_router
from .core import logging_config   # noqa: F401  (yalnızca import yeter)


app = FastAPI(title="R&D Pipeline API", version="0.1.0")

@app.get("/ping")
def ping():
    return {"msg": "pong"}

app.include_router(v1_router)

for r in app.routes:
    print("▶", r.path, r.methods)


# FastAPI instance + router montajı
# FastAPI nesnesini tanımlar, router’ları bağlar
# Neden böyle?
# core yapılandırmayı, services iş mantığını, api ise HTTP katmanını ayırır. Bu sayede ileride
# başka UI’lar eklemek (örn. CLI) kolaylaşır.