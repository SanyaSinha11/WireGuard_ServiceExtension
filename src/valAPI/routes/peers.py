from fastapi import APIRouter
from pydantic import BaseModel
from valAPI.clients.daemon_client import send

router = APIRouter(prefix="/peers", tags=["Peers"])

class PeerAddModel(BaseModel):
    interface: str = "wg0"
    public_key: str
    allowed_ips: str

class PeerRemoveModel(BaseModel):
    interface: str = "wg0"
    public_key: str

@router.post("/add")
def add_peer(payload: PeerAddModel):
    return send({
        "action":"add_peer",
        "interface": payload.interface,
        "public_key": payload.public_key,
        "allowed_ips": payload.allowed_ips
    })

@router.delete("/remove")
def remove_peer(payload: PeerRemoveModel):
    return send({
        "action":"remove_peer",
        "interface": payload.interface,
        "public_key": payload.public_key
    })

@router.get("/")
def list_peers(interface: str = "wg0"):
    return send({"action":"list_peers", "interface": interface})

@router.get("/gen-keys")
def gen_keys():
    return send({"action":"generate_keypair"})
