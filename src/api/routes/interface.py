from fastapi import APIRouter, Body
from pydantic import BaseModel
from typing import Optional
from api.clients.daemon_client import send

router = APIRouter(prefix="/interface", tags=["Interface"])

# ----------------------
# Request Models
# ----------------------
class InterfaceCreateModel(BaseModel):
    ifname: str = "wg0"
    private_key: str
    listen_port: Optional[int] = None
    address: Optional[str] = None
    mtu: Optional[int] = None
    dns: Optional[str] = None
    table: Optional[str] = None


class InterfaceDeleteModel(BaseModel):
    ifname: str = "wg0"


class InterfaceRestartModel(BaseModel):
    ifname: str = "wg0"


class InterfaceSaveModel(BaseModel):
    ifname: str = "wg0"


# ----------------------
# API Routes
# ----------------------
@router.post("/create")
def create_interface(payload: InterfaceCreateModel = Body(...)):
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
    return send({
        "action": "delete_interface",
        "ifname": payload.ifname
    })


@router.get("/list")
def list_interfaces():
    return send({"action": "list_interfaces", "detailed": True})


@router.post("/restart")
def restart_interface(payload: InterfaceRestartModel = Body(...)):
    return send({
        "action": "restart_interface",
        "ifname": payload.ifname
    })


@router.post("/save")
def save_interface_config(payload: InterfaceSaveModel = Body(...)):
    return send({
        "action": "save_interface_config",
        "ifname": payload.ifname
    })
