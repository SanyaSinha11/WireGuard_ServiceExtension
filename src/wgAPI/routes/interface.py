from fastapi import APIRouter
from ..services.wg_service import WGService

router = APIRouter(prefix="/interface", tags=["Interface"])
wg_service = WGService()

@router.post("/create")
def create_interface():
    """API: Create WireGuard interface"""
    return wg_service.create_interface()

@router.delete("/delete")
def delete_interface():
    """API: Delete WireGuard interface"""
    return wg_service.delete_interface()

@router.get("/list")
def list_interface():
    return wg_service.list_interface()