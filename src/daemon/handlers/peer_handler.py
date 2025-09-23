from daemon.utils.peer import add_peer, remove_peer, list_peers

def handle_list(ifname: str = "wg0"):
    return list_peers(ifname)

def handle_add(ifname: str, public_key: str, allowed_ips: str):
    return add_peer(ifname, public_key, allowed_ips)

def handle_remove(ifname: str, public_key: str):
    return remove_peer(ifname, public_key)
