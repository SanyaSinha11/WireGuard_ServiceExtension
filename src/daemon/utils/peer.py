import shutil
from typing import Dict, Any, List, Optional
from daemon.utils.common import run_cmd


def list_peers(ifname: str = "wg0") -> Dict[str, Any]:
    """List peers of a WireGuard interface using `wg show dump`."""
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
                "preshared_key": cols[1] if cols[1] != "(none)" else None,
                "endpoint": cols[2] if cols[2] != "(none)" else None,
                "allowed_ips": cols[3],
                "latest_handshake": cols[4],
                "transfer_rx": cols[5],
                "transfer_tx": cols[6],
                "persistent_keepalive": cols[7] if len(cols) > 7 and cols[7] != "off" else None
            })
        return {"status": "success", "peers": peers}
    return {"status": "error", "message": "wg binary not found."}


def add_peer(
    ifname: str,
    public_key: str,
    allowed_ips: str,
    preshared_key: Optional[str] = None,
    endpoint: Optional[str] = None,
    persistent_keepalive: Optional[int] = None
) -> Dict[str, Any]:
    """
    Add peer with full WireGuard configuration.
    """
    cmd = ["wg", "set", ifname, "peer", public_key, "allowed-ips", allowed_ips]

    if preshared_key:
        cmd.extend(["preshared-key", preshared_key])
    if endpoint:
        cmd.extend(["endpoint", endpoint])
    if persistent_keepalive:
        cmd.extend(["persistent-keepalive", str(persistent_keepalive)])

    return run_cmd(cmd)


def remove_peer(ifname: str, public_key: str) -> Dict[str, Any]:
    """Remove a peer from an interface."""
    return run_cmd(["wg", "set", ifname, "peer", public_key, "remove"])


def count_peers(ifname: str) -> int:
    """Return number of peers for an interface."""
    peers = list_peers(ifname)
    if peers.get("status") == "success":
        return len(peers.get("peers", []))
    return 0
