import os
import subprocess
from typing import Dict, Any, Optional, List
from daemon.utils.common import run_cmd

def create_interface(
    ifname: str,
    private_key: str,
    listen_port: Optional[int] = None,
    address: Optional[str] = None,
    mtu: Optional[int] = None,
    dns: Optional[str] = None,
    table: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create WireGuard interface with full configuration.
    """
    res = run_cmd(["ip", "link", "add", ifname, "type", "wireguard"])
    if res["status"] != "success":
        return res

    key_file = f"/tmp/{ifname}_priv.key"
    try:
        with open(key_file, "w") as f:
            f.write(private_key.strip())

        # Set private key
        res = run_cmd(["wg", "set", ifname, "private-key", key_file])
        if res["status"] != "success":
            return res

        # Listen port
        if listen_port:
            res = run_cmd(["wg", "set", ifname, "listen-port", str(listen_port)])
            if res["status"] != "success":
                return res

        # Address
        if address:
            res = run_cmd(["ip", "address", "add", address, "dev", ifname])
            if res["status"] != "success":
                return res

        # MTU
        if mtu:
            res = run_cmd(["ip", "link", "set", "dev", ifname, "mtu", str(mtu)])
            if res["status"] != "success":
                return res

        # Bring interface up
        res = run_cmd(["ip", "link", "set", "up", "dev", ifname])
        if res["status"] != "success":
            return res

        return {"status": "success", "message": f"Interface {ifname} created with configuration."}
    finally:
        if os.path.exists(key_file):
            os.remove(key_file)


def delete_interface(ifname: str) -> Dict[str, Any]:
    return run_cmd(["ip", "link", "del", ifname])


def list_interfaces(detailed: bool = True) -> Dict[str, Any]:
    """
    List WireGuard interfaces with full state, MTU, addresses, and wg config.
    """
    try:
        from pyroute2 import IPRoute, NetlinkError
        import shutil

        ipr = IPRoute()
        interfaces: List[Dict[str, Any]] = []

        # Get all WireGuard interfaces from wg binary if available
        wg_interfaces: List[str] = []
        if shutil.which("wg"):
            try:
                wg_res = subprocess.run(["wg", "show", "interfaces"], capture_output=True, text=True)
                if wg_res.returncode == 0:
                    wg_interfaces = wg_res.stdout.strip().split()
            except Exception:
                pass

        # Iterate through all links via pyroute2
        for link in ipr.get_links():
            ifname = link.get_attr("IFLA_IFNAME")
            linkinfo = link.get_attr("IFLA_LINKINFO")
            kind = linkinfo.get_attr("IFLA_INFO_KIND") if linkinfo else None
            if kind != "wireguard":
                continue

            iface: Dict[str, Any] = {
                "index": link["index"],
                "ifname": ifname,
                "state": link.get_attr("IFLA_OPERSTATE") or "DOWN",
                "mtu": link.get_attr("IFLA_MTU")
            }

            # Addresses
            addresses: List[str] = []
            try:
                for addr in ipr.get_addr(index=link["index"]):
                    ip = addr.get_attr("IFA_ADDRESS")
                    prefix = addr["prefixlen"]
                    addresses.append(f"{ip}/{prefix}")
            except NetlinkError:
                pass
            iface["addresses"] = addresses

            # WireGuard config
            if detailed and ifname in wg_interfaces:
                try:
                    wg_res = subprocess.run(["wg", "show", ifname], capture_output=True, text=True)
                    iface["config"] = wg_res.stdout.strip() if wg_res.returncode == 0 else ""
                except Exception:
                    iface["config"] = ""
            else:
                iface["config"] = ""

            interfaces.append(iface)

        return {"status": "success", "interfaces": interfaces}

    except Exception as e:
        return {"status": "error", "message": f"list_interfaces failed: {e}"}

def restart_interface(ifname: str = "wg0") -> Dict[str, Any]:
    """
    Restart a WireGuard interface safely.
    Brings the interface down and back up.
    """
    down_res = run_cmd(["ip", "link", "set", "dev", ifname, "down"])
    if down_res.get("status") != "success":
        return {"status": "error", "message": f"Failed to bring down {ifname}: {down_res.get('stderr', '')}"}

    up_res = run_cmd(["ip", "link", "set", "dev", ifname, "up"])
    if up_res.get("status") != "success":
        return {"status": "error", "message": f"Failed to bring up {ifname}: {up_res.get('stderr', '')}"}

    return {"status": "success", "message": f"Interface {ifname} restarted successfully."}
