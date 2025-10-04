from daemon.utils.peer import add_peer, remove_peer, list_peers


def handle_list(ifname: str = "wg0"):
    """Handle listing peers for an interface."""
    return list_peers(ifname)


def handle_add(
    ifname: str,
    public_key: str,
    allowed_ips: str,
    preshared_key: str = None,
    endpoint: str = None,
    persistent_keepalive: int = None
):
    """Handle adding a peer with extended configuration options."""
    return add_peer(
        ifname=ifname,
        public_key=public_key,
        allowed_ips=allowed_ips,
        preshared_key=preshared_key,
        endpoint=endpoint,
        persistent_keepalive=persistent_keepalive,
    )


def handle_remove(ifname: str, public_key: str):
    """Handle removing a peer from an interface."""
    return remove_peer(ifname, public_key)
