from fastapi import APIRouter, Body, Query
from pydantic import BaseModel
from typing import Optional
from api.clients.daemon_client import send

router = APIRouter(prefix="/peers", tags=["Peers"])

class PeerAddModel(BaseModel):
    """
    Model for adding a new peer with full configuration.
    """
    interface: str = "wg0"
    public_key: str
    preshared_key: Optional[str] = None
    allowed_ips: str
    endpoint: Optional[str] = None             # e.g., "192.168.1.5:51820" or "vpn.example.com:51820"
    persistent_keepalive: Optional[int] = None # in seconds


class PeerRemoveModel(BaseModel):
    interface: str = "wg0"
    public_key: str


@router.post("/add")
def add_peer(payload: PeerAddModel = Body(...)):
    """Add a new peer to a WireGuard interface with full config"""
    return send({
        "action": "add_peer",
        "interface": payload.interface,
        "public_key": payload.public_key,
        "preshared_key": payload.preshared_key,
        "allowed_ips": payload.allowed_ips,
        "endpoint": payload.endpoint,
        "persistent_keepalive": payload.persistent_keepalive
    })


@router.delete("/remove")
def remove_peer(payload: PeerRemoveModel = Body(...)):
    """Remove a peer from an interface"""
    return send({
        "action": "remove_peer",
        "interface": payload.interface,
        "public_key": payload.public_key
    })


@router.get("/")
def list_peers(interface: str = Query("wg0")):
    """List peers on a WireGuard interface with detailed info"""
    return send({"action": "list_peers", "interface": interface})


@router.get("/gen-keys")
def generate_keys():
    """Generate a WireGuard private/public keypair"""
    return send({"action": "generate_keypair"})
