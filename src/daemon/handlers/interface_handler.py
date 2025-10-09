from daemon.utils.interface import create_interface, delete_interface, list_interfaces, restart_interface, save_interface_config

def handle_create(config: dict):
    """
    Handle interface creation.
    Expects a full configuration dictionary from API layer.
    """
    return create_interface(
        ifname=config.get("ifname", "wg0"),
        private_key=config.get("private_key"),
        listen_port=config.get("listen_port"),
        address=config.get("address"),
        mtu=config.get("mtu"),
        dns=config.get("dns"),
        table=config.get("table")
    )

def handle_delete(ifname: str):
    return delete_interface(ifname)

def handle_list(detailed: bool = True):
    return list_interfaces(detailed)

def handle_restart(ifname: str):
    return restart_interface(ifname)

def handle_save(ifname: str):
    return save_interface_config(ifname)
