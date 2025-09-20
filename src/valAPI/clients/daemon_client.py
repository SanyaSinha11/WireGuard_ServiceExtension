import socket
import json
import os
from typing import Dict, Any

DEFAULT_SOCKET = os.environ.get("VALDAEMON_SOCKET", "/run/valdaemon.sock")
FALLBACK_SOCKET = "/tmp/valdaemon.sock"

def _choose_socket():
    if os.path.exists(DEFAULT_SOCKET):
        return DEFAULT_SOCKET
    if os.path.exists(FALLBACK_SOCKET):
        return FALLBACK_SOCKET
    return DEFAULT_SOCKET

def send(payload: Dict[str, Any], socket_path: str = None, timeout: float = 5.0) -> Dict[str, Any]:
    path = socket_path or _choose_socket()
    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.settimeout(timeout)
        client.connect(path)
    except FileNotFoundError:
        return {"status": "error", "message": f"Socket not found at {path}. Is valDaemon running?"}
    except PermissionError:
        return {"status": "error", "message": f"Permission denied connecting to socket {path}."}
    except Exception as e:
        return {"status": "error", "message": f"Connection error to {path}: {e}"}

    try:
        client.sendall(json.dumps(payload).encode("utf-8"))
        resp = b""
        while True:
            try:
                chunk = client.recv(65536)
                if not chunk:
                    break
                resp += chunk
            except socket.timeout:
                break
        if not resp:
            return {"status":"error","message":"empty response from daemon"}
        return json.loads(resp.decode("utf-8"))
    except Exception as e:
        return {"status":"error","message":f"send/recv error: {e}"}
    finally:
        try:
            client.close()
        except Exception:
            pass
