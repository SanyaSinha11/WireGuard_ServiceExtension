from fastapi import APIRouter, Body
from pydantic import BaseModel
from api.clients.daemon_client import send

router = APIRouter(prefix="/interface", tags=["Interface"])


class InterfaceModel(BaseModel):
    name: str = "wg0"


@router.post("/create")
def create_interface(payload: InterfaceModel = Body(...)):
    """Create a WireGuard interface"""
    return send({"action": "create_interface", "interface": payload.name})


@router.delete("/delete")
def delete_interface(payload: InterfaceModel = Body(...)):
    """Delete a WireGuard interface"""
    return send({"action": "delete_interface", "interface": payload.name})


@router.get("/list")
def list_interfaces():
    """List existing WireGuard interfaces"""
    return send({"action": "list_interfaces"})
