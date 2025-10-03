from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from routers import server_config,api_proxy,peer_config  # import the router

app = FastAPI()

# Static files
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

# Templates
templates = Jinja2Templates(directory="templates")

# Root route
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("authentication/login.html", {"request": request})

# Include server config router with prefix
app.include_router(server_config.router, prefix="/server-config", tags=["Server Configurations"])
app.include_router(peer_config.router, prefix="/peer-mng", tags=["Peer Management"])



# Include API proxy router - this hides the backend API from frontend clients
app.include_router(api_proxy.router, tags=["Frontend API Proxy"])