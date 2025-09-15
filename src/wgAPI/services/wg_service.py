from pyroute2 import IPRoute, WireGuard
import base64
import os
import subprocess

class WGService:
    def __init__(self, interface: str = "wg0"):
        self.interface = interface

    def _check_privileges(self):
        """Check if process has NET_ADMIN privilege"""
        if os.geteuid() != 0:
            return False
        return True

    def _run_cmd(self, cmd: list):
        """Fallback: run shell command with sudo if not root"""
        try:
            result = subprocess.run(
                ["sudo"] + cmd,
                check=True,
                capture_output=True,
                text=True
            )
            return {"status": "success", "message": result.stdout.strip() or "Command executed"}
        except subprocess.CalledProcessError as e:
            return {"status": "error", "message": e.stderr.strip()}

    def list_interface(self):
        """List WireGuard interfaces"""
        try:
            with IPRoute() as ipr:
                links = ipr.get_links()
                wg_links = [
                    {
                        "index": link["index"],
                        "ifname": link.get_attr("IFLA_IFNAME"),
                        "state": link.get_attr("IFLA_OPERSTATE"),
                        "kind": link.get_attr("IFLA_LINKINFO")
                        and link.get_attr("IFLA_LINKINFO").get_attr("IFLA_INFO_KIND"),
                    }
                    for link in links
                    if link.get_attr("IFLA_LINKINFO")
                    and link.get_attr("IFLA_LINKINFO").get_attr("IFLA_INFO_KIND") == "wireguard"
                ]
            return {"status": "success", "interfaces": wg_links}
        except Exception as e:
            return {"status": "error", "message": str(e)}
        
    def create_interface(self):
        """Create a WireGuard interface like `ip link add wg0 type wireguard`"""
        try:
            if not self._check_privileges():
                # fallback to shell command
                return self._run_cmd(["ip", "link", "add", self.interface, "type", "wireguard"])

            with IPRoute() as ipr:
                ipr.link("add", ifname=self.interface, kind="wireguard")
            return {"status": "success", "message": f"Interface {self.interface} created"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def delete_interface(self):
        """Delete the WireGuard interface"""
        try:
            if not self._check_privileges():
                return self._run_cmd(["ip", "link", "del", self.interface])

            with IPRoute() as ipr:
                idx_list = ipr.link_lookup(ifname=self.interface)
                if not idx_list:
                    return {"status": "error", "message": f"Interface {self.interface} not found"}
                ipr.link("del", index=idx_list[0])
            return {"status": "success", "message": f"Interface {self.interface} deleted"}
        except Exception as e:
            return {"status": "error", "message": str(e)}


    def list_peers(self):
        """List peers connected to the interface like `wg show wg0`"""
        try:
            with WireGuard() as wg:
                peers = wg.info(self.interface).get("peers", [])
            return {"status": "success", "peers": peers}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def add_peer(self, public_key: str, allowed_ips: str):
        """Add a new peer with given public key and AllowedIPs"""
        try:
            with WireGuard() as wg:
                wg.set(self.interface, peer={
                    "public_key": base64.b64decode(public_key),
                    "allowed_ips": [(allowed_ips, 32)]
                })
            return {"status": "success", "message": f"Peer {public_key} added"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def remove_peer(self, public_key: str):
        """Remove a peer by public key"""
        try:
            with WireGuard() as wg:
                wg.set(self.interface, peer={
                    "public_key": base64.b64decode(public_key),
                    "remove": True
                })
            return {"status": "success", "message": f"Peer {public_key} removed"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
