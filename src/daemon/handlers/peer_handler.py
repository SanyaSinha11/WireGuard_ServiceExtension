from valDaemon.utils.wg_service import add_peer, remove_peer, list_peers

def handle_list(iface: str = "wg0"):
    return list_peers(iface)

def handle_add(iface: str, public_key: str, allowed_ips: str):
    return add_peer(iface, public_key, allowed_ips)

def handle_remove(iface: str, public_key: str):
    return remove_peer(iface, public_key)
