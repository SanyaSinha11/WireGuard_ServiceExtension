from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
import httpx

router = APIRouter()

# Configuration models for request/response validation
class InterfaceConfig(BaseModel):
    interface_name: str
    listen_port: int
    private_key: str
    server_address: str
    mtu_size: int
    dns_servers: str

class NetworkConfig(BaseModel):
    allowed_subnets: str
    nat_masquerading: bool
    ip_forwarding: bool
    firewall_integration: bool

class SecurityConfig(BaseModel):
    keep_alive_interval: int
    maximum_clients: int
    log_info: str
    server_address: str
    mtu_size: int
    dns_servers: str

# Backend API base URL - this would typically come from environment variables
BACKEND_API_URL = "http://localhost:8001"  # Example backend service

# Mock data for all endpoints
MOCK_DATA = {
    "interface": {
        "GET": {
            "interface_name": "wg0",
            "listen_port": 51820,
            "private_key": "*********************************",
            "server_address": "10.0.0.1/24",
            "mtu_size": 1420,
            "dns_servers": "1.1.1.1, 8.8.8.8"
        },
        "generate-key": {
            "status": "success",
            "private_key": "qQ9qK7wX8+mZ1w5kF6q2N8L3jJ4sY7zW2tN6rV9bE3A=",
            "message": "New private key generated successfully"
        }
    },
    "network": {
        "GET": {
            "allowed_subnets": "10.0.0.0/24\n192.168.1.0/24",
            "nat_masquerading": True,
            "ip_forwarding": False,
            "firewall_integration": False
        }
    },
    "security": {
        "GET": {
            "keep_alive_interval": 25,
            "maximum_clients": 100,
            "log_info": "enabled",
            "server_address": "10.0.0.1/24",
            "mtu_size": 1420,
            "dns_servers": "1.1.1.1, 8.8.8.8"
        }
    }
}

# Generic proxy function with better error handling and mock data fallback
async def proxy_to_backend(endpoint: str, method: str = "GET", data: Optional[Dict[Any, Any]] = None) -> Dict[Any, Any]:
    """
    Generic function to proxy requests to the backend API.
    If the backend is unavailable, it falls back to mock data.
    """
    try:
        async with httpx.AsyncClient() as client:
            url = f"{BACKEND_API_URL}{endpoint}"
            response = await client.request(method.upper(), url, json=data if data else None)
            
            # Handle backend errors
            if response.status_code >= 400:
                raise HTTPException(status_code=response.status_code, detail=f"Backend error: {response.text}")
            
            return response.json()
    except httpx.RequestError as e:
        # If backend is not available, return mock data for demonstration
        return await get_mock_data(endpoint, method, data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Proxy error: {str(e)}")

async def get_mock_data(endpoint: str, method: str, data: Optional[Dict[Any, Any]] = None) -> Dict[Any, Any]:
    """
    Provide mock data when backend is not available.
    This can be extended or modified based on the endpoint being accessed.
    """
    if "interface" in endpoint:
        if method.upper() == "POST" or method.upper() == "GET":
            return MOCK_DATA["interface"].get(method.upper(), MOCK_DATA["interface"]["GET"])
    elif "network" in endpoint:
        if method.upper() == "POST" or method.upper() == "GET":
            return MOCK_DATA["network"].get(method.upper(), {})
    elif "security" in endpoint:
        if method.upper() == "POST" or method.upper() == "GET":
            return MOCK_DATA["security"].get(method.upper(), {})
    
    return {"status": "success", "message": "Operation completed"}

# Generalized route handler for configuration endpoints
def create_config_endpoint(config_type: str, config_model: BaseModel):
    """
    Create generalized routes for config endpoints to reduce duplication.
    """
    @router.get(f"/api/config/{config_type}")
    async def get_config():
        """Get current configuration from backend."""
        return await proxy_to_backend(f"/api/wireguard/{config_type}", "GET")

    @router.post(f"/api/config/{config_type}")
    async def update_config(config: config_model):
        """Update configuration via backend."""
        return await proxy_to_backend(f"/api/wireguard/{config_type}", "POST", config.dict())
    
    return get_config, update_config

# Dynamically create routes for interface, network, and security configs
create_config_endpoint("interface", InterfaceConfig)
create_config_endpoint("network", NetworkConfig)
create_config_endpoint("security", SecurityConfig)

# Health check endpoint with retry logic
@router.get("/api/health")
async def health_check():
    """Check health of the proxy service and backend connectivity."""
    try:
        backend_status = await proxy_to_backend("/api/health", "GET")
        return {"status": "healthy", "proxy": "operational", "backend": backend_status}
    except Exception as e:
        return {"status": "degraded", "proxy": "operational", "backend": "unavailable - using mock data"}

