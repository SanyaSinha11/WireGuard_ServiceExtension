from fastapi import FastAPI
from .routes import interface, peers

app = FastAPI(
    title="WireGuard API Service",
    description="API wrapper around WireGuard using pyroute2",
    version="1.0.0"
)

# Register routers
app.include_router(interface.router)
app.include_router(peers.router)

@app.get("/")
def read_root():
    return {"message": "WireGuard API is running! Visit /docs for API docs."}