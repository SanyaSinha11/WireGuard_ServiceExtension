from fastapi import APIRouter, Body
from pydantic import BaseModel
from typing import Optional
from api.clients.daemon_client import send

router = APIRouter(prefix="/interface", tags=["Interface"])


# ----------------------
# Request Models
# ----------------------
class InterfaceCreateModel(BaseModel):
    """
    Model for creating a WireGuard interface.
    """
    ifname: str = "wg0"
    private_key: str
    listen_port: Optional[int] = None
    address: Optional[str] = None       # e.g., "10.0.0.1/24"
    mtu: Optional[int] = None
    dns: Optional[str] = None
    table: Optional[str] = None

class InterfaceDeleteModel(BaseModel):
    ifname: str = "wg0"

class InterfaceRestartModel(BaseModel):
    name: str = "wg0"

class InterfaceSaveModel(BaseModel):
    name: str = "wg0"

# ----------------------
# API Routes
# ----------------------
@router.post("/create")
def create_interface(payload: InterfaceCreateModel = Body(...)):
    """
    Create a new WireGuard interface with full configuration.
    """
    return send({
        "action": "create_interface",
        "ifname": payload.ifname,
        "private_key": payload.private_key,
        "listen_port": payload.listen_port,
        "address": payload.address,
        "mtu": payload.mtu,
        "dns": payload.dns,
        "table": payload.table
    })


@router.delete("/delete")
def delete_interface(payload: InterfaceDeleteModel = Body(...)):
    """
    Delete a WireGuard interface.
    """
    return send({
        "action": "delete_interface",
        "ifname": payload.ifname
    })


@router.get("/list")
def list_interfaces():
    """
    List existing WireGuard interfaces with detailed configuration and status.
    Each interface should include:
      - ifname
      - state (up/down)
      - MTU
      - addresses
      - WireGuard config
    """
    return send({"action": "list_interfaces", "detailed": True})

@router.post("/restart")
def restart_interface(payload: InterfaceRestartModel = Body(...)):
    """
    Restart a WireGuard interface (down and up again).
    """
    return send({
        "action": "restart_interface",
        "interface": payload.name
    })

@router.post("/save")
def save_interface_config(payload: InterfaceSaveModel = Body(...)):
    """
    Save the live WireGuard interface configuration to /etc/wireguard/<ifname>.conf
    """
    return send({
        "action": "save_interface_config",
        "interface": payload.name
    })