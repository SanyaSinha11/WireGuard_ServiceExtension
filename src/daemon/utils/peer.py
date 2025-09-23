import shutil
from typing import Dict, Any, List
from daemon.utils.common import run_cmd

def list_peers(ifname: str = "wg0") -> Dict[str, Any]:
    """List peers of a WireGuard interface."""
    if shutil.which("wg"):
        res = run_cmd(["wg", "show", ifname, "dump"])
        if res.get("status") != "success":
            return res
        lines = res.get("stdout", "").splitlines()
        peers: List[Dict[str, Any]] = []
        for line in lines[1:]:
            cols = line.split()
            peers.append({
                "public_key": cols[0],
                "preshared_key": cols[1],
                "endpoint": cols[2],
                "allowed_ips": cols[3],
                "latest_handshake": cols[4],
                "transfer_rx": cols[5],
                "transfer_tx": cols[6],
                "persistent_keepalive": cols[7] if len(cols) > 7 else None
            })
        return {"status": "success", "peers": peers}
    return {"status": "error", "message": "wg binary not found."}


def add_peer(ifname: str, public_key: str, allowed_ips: str) -> Dict[str, Any]:
    return run_cmd(["wg", "set", ifname, "peer", public_key, "allowed-ips", allowed_ips])


def remove_peer(ifname: str, public_key: str) -> Dict[str, Any]:
    return run_cmd(["wg", "set", ifname, "peer", public_key, "remove"])
