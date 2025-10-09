import os
import shutil
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
    Create and configure a WireGuard interface with full options.
    Includes key setup, address, MTU, DNS, and routing table assignment.
    """

    # --- Sanity checks ---
    if not ifname or not private_key:
        return {"status": "error", "message": "Interface name and private_key are required."}

    # --- Step 1: Create the WireGuard link ---
    res = run_cmd(["ip", "link", "add", ifname, "type", "wireguard"])
    if res["status"] != "success":
        # Handle case where interface already exists
        if "File exists" in res.get("stderr", ""):
            return {"status": "error", "message": f"Interface {ifname} already exists."}
        return res

    key_file = f"/tmp/{ifname}_priv.key"
    try:
        # --- Step 2: Write private key to temp file ---
        with open(key_file, "w") as f:
            f.write(private_key.strip())

        # --- Step 3: Apply WireGuard settings ---
        res = run_cmd(["wg", "set", ifname, "private-key", key_file])
        if res["status"] != "success":
            return res

        # --- Step 4: Set listen port ---
        if listen_port:
            res = run_cmd(["wg", "set", ifname, "listen-port", str(listen_port)])
            if res["status"] != "success":
                return res

        # --- Step 5: Assign IP address ---
        if address:
            res = run_cmd(["ip", "address", "add", address, "dev", ifname])
            if res["status"] != "success":
                return res

        # --- Step 6: Set MTU ---
        if mtu:
            res = run_cmd(["ip", "link", "set", "dev", ifname, "mtu", str(mtu)])
            if res["status"] != "success":
                return res

        # --- Step 7: Set DNS (optional, system dependent) ---
        # This doesn't modify wg config directly, but can be useful for resolvconf integration.
        if dns:
            resolv_conf = f"/etc/resolv.conf"
            try:
                with open(resolv_conf, "a") as f:
                    f.write(f"\n# Added by wg-daemon for {ifname}\nnameserver {dns}\n")
            except PermissionError:
                pass  # Ignore DNS write errors if not root

        # --- Step 8: Bring interface up ---
        res = run_cmd(["ip", "link", "set", "up", "dev", ifname])
        if res["status"] != "success":
            return res

        # --- Step 9: Optionally assign table for routing ---
        if table:
            run_cmd(["ip", "rule", "add", "from", address.split("/")[0], "table", table])

        return {"status": "success", "message": f"Interface {ifname} created successfully."}

    finally:
        if os.path.exists(key_file):
            os.remove(key_file)


def delete_interface(ifname: str) -> Dict[str, Any]:
    """Delete a WireGuard interface."""
    return run_cmd(["ip", "link", "del", ifname])


def list_interfaces(detailed: bool = True) -> Dict[str, Any]:
    """
    List WireGuard interfaces with full details:
    - Interface name, state, MTU
    - Assigned addresses
    - WireGuard configuration
    """
    try:
        from pyroute2 import IPRoute, NetlinkError
        ipr = IPRoute()
        interfaces: List[Dict[str, Any]] = []

        # Get all WireGuard interfaces via wg binary
        wg_interfaces: List[str] = []
        if shutil.which("wg"):
            try:
                wg_res = subprocess.run(["wg", "show", "interfaces"], capture_output=True, text=True)
                if wg_res.returncode == 0:
                    wg_interfaces = wg_res.stdout.strip().split()
            except Exception:
                pass

        # Iterate through all system links
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
                "mtu": link.get_attr("IFLA_MTU"),
                "addresses": []
            }

            # Addresses
            try:
                for addr in ipr.get_addr(index=link["index"]):
                    ip = addr.get_attr("IFA_ADDRESS")
                    prefix = addr["prefixlen"]
                    iface["addresses"].append(f"{ip}/{prefix}")
            except NetlinkError:
                pass

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
    """Restart a WireGuard interface safely."""
    down_res = run_cmd(["ip", "link", "set", "dev", ifname, "down"])
    if down_res.get("status") != "success":
        return {"status": "error", "message": f"Failed to bring down {ifname}: {down_res.get('stderr', '')}"}

    up_res = run_cmd(["ip", "link", "set", "dev", ifname, "up"])
    if up_res.get("status") != "success":
        return {"status": "error", "message": f"Failed to bring up {ifname}: {up_res.get('stderr', '')}"}

    return {"status": "success", "message": f"Interface {ifname} restarted successfully."}


def save_interface_config(ifname: str = "wg0") -> Dict[str, Any]:
    """
    Save current WireGuard interface configuration to /etc/wireguard/<ifname>.conf.
    Equivalent to: wg showconf <ifname> > /etc/wireguard/<ifname>.conf
    """
    if not shutil.which("wg"):
        return {"status": "error", "message": "wg binary not found."}

    conf_dir = "/etc/wireguard"
    conf_path = os.path.join(conf_dir, f"{ifname}.conf")

    try:
        os.makedirs(conf_dir, exist_ok=True)
        res = run_cmd(["wg", "showconf", ifname])

        if res.get("status") != "success":
            return {"status": "error", "message": f"Failed to get config for {ifname}: {res.get('stderr', '')}"}

        with open(conf_path, "w") as f:
            f.write(res["stdout"])

        return {"status": "success", "message": f"Configuration for {ifname} saved to {conf_path}"}

    except PermissionError:
        return {"status": "error", "message": f"Permission denied writing to {conf_path}. Run as root."}
    except Exception as e:
        return {"status": "error", "message": str(e)}
