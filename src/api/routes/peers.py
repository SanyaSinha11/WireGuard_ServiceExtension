from fastapi import APIRouter, Body, Query
from pydantic import BaseModel
from api.clients.daemon_client import send

router = APIRouter(prefix="/peers", tags=["Peers"])


class PeerAddModel(BaseModel):
    interface: str = "wg0"
    public_key: str
    allowed_ips: str


class PeerRemoveModel(BaseModel):
    interface: str = "wg0"
    public_key: str


@router.post("/add")
def add_peer(payload: PeerAddModel = Body(...)):
    """Add a new peer to an interface"""
    return send({
        "action": "add_peer",
        "interface": payload.interface,
        "public_key": payload.public_key,
        "allowed_ips": payload.allowed_ips
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
    """List peers on a WireGuard interface"""
    return send({"action": "list_peers", "interface": interface})


@router.get("/gen-keys")
def generate_keys():
    """Generate a WireGuard private/public keypair"""
    return send({"action": "generate_keypair"})
