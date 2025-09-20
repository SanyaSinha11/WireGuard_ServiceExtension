from fastapi import APIRouter
from pydantic import BaseModel
from valAPI.clients.daemon_client import send

router = APIRouter(prefix="/interface", tags=["Interface"])

class InterfaceModel(BaseModel):
    name: str = "wg0"

@router.post("/create")
def create(payload: InterfaceModel):
    return send({"action":"create_interface", "interface": payload.name})

@router.delete("/delete")
def delete(payload: InterfaceModel):
    return send({"action":"delete_interface", "interface": payload.name})

@router.get("/list")
def list_interfaces():
    return send({"action":"list_interfaces"})
