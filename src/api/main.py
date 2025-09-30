from fastapi import FastAPI
from api.routes import interface, peers
from api.clients.daemon_client import send

app = FastAPI(title="ValGuard API (REST) - WireGuard extension",
              description="REST endpoints that forward commands to daemon via a Unix socket.",
              version="0.1.0")

app.include_router(interface.router)
app.include_router(peers.router)

@app.get("/")
def root():
    """
    Root endpoint with daemon health check.
    Returns daemon status and instructions.
    """
    # Send a simple "list_interfaces" action as health check
    resp = send({"action": "list_interfaces"}, timeout=2.0)
    print(resp)
    if resp.get("status") == "success":
        return {
            "message": "ValGuard API running. Daemon is reachable.",
            "daemon_status": resp
        }
    else:
        return {
            "message": "ValGuard API running. Daemon is NOT reachable.",
            "daemon_status": resp
        }
