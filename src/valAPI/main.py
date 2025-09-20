from fastapi import FastAPI
from valAPI.routes import interface, peers

app = FastAPI(title="ValAPI (REST) - WireGuard extension",
              description="REST endpoints that forward commands to valDaemon via a Unix socket.",
              version="0.1.0")

app.include_router(interface.router)
app.include_router(peers.router)

@app.get("/")
def root():
    return {"message":"ValAPI running. Visit /docs for Swagger UI."}
