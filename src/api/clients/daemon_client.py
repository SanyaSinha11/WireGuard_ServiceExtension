import socket
import json
import os
from typing import Dict, Any

DEFAULT_SOCKET = os.environ.get("DAEMON_SOCKET", "/run/daemon.sock")
FALLBACK_SOCKET = "/tmp/daemon.sock"


def _choose_socket() -> str:
    if os.path.exists(DEFAULT_SOCKET):
        return DEFAULT_SOCKET
    if os.path.exists(FALLBACK_SOCKET):
        return FALLBACK_SOCKET
    return DEFAULT_SOCKET


def send(payload: Dict[str, Any], socket_path: str = None, timeout: float = 5.0) -> Dict[str, Any]:
    """
    Send a JSON payload to the daemon via UNIX socket.
    Uses newline-delimited JSON protocol (one request/response per line).
    """
    path = socket_path or _choose_socket()
    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.settimeout(timeout)
        client.connect(path)
    except FileNotFoundError:
        return {"status": "error", "message": f"Socket not found at {path}. Is Daemon running?"}
    except PermissionError:
        return {"status": "error", "message": f"Permission denied connecting to socket {path}."}
    except Exception as e:
        return {"status": "error", "message": f"Connection error to {path}: {e}"}

    try:
        # Send JSON + newline so daemon knows when request ends
        client.sendall((json.dumps(payload) + "\n").encode("utf-8"))

        # Read until newline (one full response)
        resp = b""
        while not resp.endswith(b"\n"):
            chunk = client.recv(65536)
            if not chunk:
                break
            resp += chunk

        if not resp.strip():
            return {"status": "error", "message": "empty response from daemon"}

        return json.loads(resp.decode("utf-8").strip())
    except Exception as e:
        return {"status": "error", "message": f"send/recv error: {e}"}
    finally:
        try:
            client.close()
        except Exception:
            pass
