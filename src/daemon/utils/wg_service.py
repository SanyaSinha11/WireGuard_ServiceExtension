import os
import shutil
import subprocess
from typing import Dict, Any, List

def _is_root() -> bool:
    return os.geteuid() == 0

def _run_cmd(cmd: List[str]) -> Dict[str, Any]:
    """
    Run a command. If not root and sudo exists, prefix with sudo.
    Returns dict with status, stdout/stderr.
    """
    prefix = []
    if not _is_root():
        if shutil.which("sudo"):
            prefix = ["sudo"]
        else:
            return {"status": "error", "message": "Root required and sudo not available."}
    try:
        proc = subprocess.run(prefix + cmd, capture_output=True, text=True)
    except Exception as e:
        return {"status": "error", "message": f"Failed to run {prefix + cmd}: {e}"}

    if proc.returncode != 0:
        return {
            "status": "error",
            "message": f"Command failed: {' '.join(prefix + cmd)}",
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "rc": proc.returncode
        }
    return {"status": "success", "stdout": proc.stdout, "stderr": proc.stderr, "rc": proc.returncode}


# ----------------------------
# Interface functions
# ----------------------------
def create_interface(ifname: str = "wg0") -> Dict[str, Any]:
    """
    Create WireGuard interface. Prefer pyroute2 when root; otherwise use `ip` via sudo.
    """
    if _is_root():
        try:
            from pyroute2 import IPRoute
            with IPRoute() as ipr:
                ipr.link("add", ifname=ifname, kind="wireguard")
                idx = ipr.link_lookup(ifname=ifname)
                if idx:
                    ipr.link("set", index=idx[0], state="up")
            return {"status": "success", "message": f"Interface {ifname} created (pyroute2)"}
        except Exception as e:
            # fallback to ip
            return {"status": "error", "message": f"pyroute2 failed: {e}"}
    else:
        return _run_cmd(["ip", "link", "add", ifname, "type", "wireguard"])


def delete_interface(ifname: str = "wg0") -> Dict[str, Any]:
    if _is_root():
        try:
            from pyroute2 import IPRoute
            with IPRoute() as ipr:
                idx = ipr.link_lookup(ifname=ifname)
                if not idx:
                    return {"status": "error", "message": f"{ifname} not found"}
                ipr.link("del", index=idx[0])
            return {"status": "success", "message": f"Interface {ifname} deleted (pyroute2)"}
        except Exception as e:
            return {"status": "error", "message": f"pyroute2 delete failed: {e}"}
    else:
        return _run_cmd(["ip", "link", "del", ifname])


def list_interfaces() -> Dict[str, Any]:
    try:
        from pyroute2 import IPRoute
        with IPRoute() as ipr:
            links = ipr.get_links()
            wg_links = []
            for link in links:
                linkinfo = link.get_attr("IFLA_LINKINFO") if link.get_attr("IFLA_LINKINFO") else None
                info_kind = linkinfo.get_attr("IFLA_INFO_KIND") if linkinfo else None
                if info_kind == "wireguard":
                    wg_links.append({
                        "index": link["index"],
                        "ifname": link.get_attr("IFLA_IFNAME"),
                        "state": link.get_attr("IFLA_OPERSTATE")
                    })
        return {"status": "success", "interfaces": wg_links}
    except Exception as e:
        return {"status": "error", "message": f"list_interfaces error: {e}"}


# ----------------------------
# Peer functions
# ----------------------------
def list_peers(ifname: str = "wg0") -> Dict[str, Any]:
    # use wg dump via wg binary (compatible)
    if shutil.which("wg"):
        res = _run_cmd(["wg", "show", ifname, "dump"])
        if res.get("status") != "success":
            return res
        dump = res.get("stdout", "")
        if not dump.strip():
            return {"status": "success", "peers": []}
        lines = dump.strip().splitlines()
        # skip header (interface info)
        peers = []
        for line in lines[1:]:
            cols = line.split()
            peers.append({"raw": line, "public_key": cols[0] if cols else None})
        return {"status": "success", "peers": peers}
    else:
        # try pyroute2 WireGuard if root
        if _is_root():
            try:
                from pyroute2 import WireGuard
                with WireGuard() as wg:
                    info = wg.info(ifname)
                return {"status": "success", "peers": info.get("peers", [])}
            except Exception as e:
                return {"status": "error", "message": f"pyroute2 WireGuard error: {e}"}
        return {"status": "error", "message": "wg binary not found and not root for pyroute2."}


def add_peer(ifname: str, public_key: str, allowed_ips: str) -> Dict[str, Any]:
    # Prefer wg binary (widely available)
    if shutil.which("wg"):
        return _run_cmd(["wg", "set", ifname, "peer", public_key, "allowed-ips", allowed_ips])
    else:
        if _is_root():
            try:
                from pyroute2 import WireGuard
                with WireGuard() as wg:
                    wg.set(ifname, peer={"public_key": public_key.encode(), "allowed_ips": [(allowed_ips, 32)]})
                return {"status": "success", "message": "Peer added via pyroute2"}
            except Exception as e:
                return {"status": "error", "message": f"pyroute2 add_peer failed: {e}"}
        return {"status": "error", "message": "wg binary not found and not root."}


def remove_peer(ifname: str, public_key: str) -> Dict[str, Any]:
    if shutil.which("wg"):
        return _run_cmd(["wg", "set", ifname, "peer", public_key, "remove"])
    else:
        if _is_root():
            try:
                from pyroute2 import WireGuard
                with WireGuard() as wg:
                    wg.set(ifname, peer={"public_key": public_key.encode(), "remove": True})
                return {"status": "success", "message": "Peer removed via pyroute2"}
            except Exception as e:
                return {"status": "error", "message": f"pyroute2 remove_peer failed: {e}"}
        return {"status": "error", "message": "wg binary not found and not root."}


def generate_keypair() -> Dict[str, Any]:
    if not shutil.which("wg"):
        return {"status": "error", "message": "wg binary required to generate keys."}
    try:
        p1 = subprocess.Popen(["wg", "genkey"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        priv, err1 = p1.communicate(timeout=3)
        if p1.returncode != 0:
            return {"status": "error", "message": f"wg genkey failed: {err1}"}
        p2 = subprocess.Popen(["wg", "pubkey"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        pub, err2 = p2.communicate(input=priv, timeout=3)
        if p2.returncode != 0:
            return {"status": "error", "message": f"wg pubkey failed: {err2}"}
        return {"status": "success", "private_key": priv.strip(), "public_key": pub.strip()}
    except Exception as e:
        return {"status": "error", "message": f"keygen error: {e}"}
