from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard/dashboard.html", {"request": request})

@router.get("/interface", response_class=HTMLResponse)
async def config_interface(request: Request):
    return templates.TemplateResponse("dashboard/configuration/interface.html", {"request": request})

@router.get("/network", response_class=HTMLResponse)
async def config_network(request: Request):
    return templates.TemplateResponse("dashboard/configuration/network.html", {"request": request})

@router.get("/security", response_class=HTMLResponse)
async def config_security(request: Request):
    return templates.TemplateResponse("dashboard/configuration/security.html", {"request": request})
