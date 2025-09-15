from fastapi import APIRouter
from ..services.wg_service import WGService

router = APIRouter(prefix="/peers", tags=["Peers"])
wg_service = WGService()

@router.get("/")
def list_peers():
    """API: List peers connected to the interface"""
    return wg_service.list_peers()

@router.post("/add")
def add_peer(public_key: str, allowed_ips: str):
    """
    API: Add a new peer
    - public_key: Base64 encoded peer public key
    - allowed_ips: IP range allowed for peer (e.g. 10.0.0.2/32)
    """
    return wg_service.add_peer(public_key, allowed_ips)

@router.delete("/remove")
def remove_peer(public_key: str):
    """
    API: Remove an existing peer by public key
    """
    return wg_service.remove_peer(public_key)
