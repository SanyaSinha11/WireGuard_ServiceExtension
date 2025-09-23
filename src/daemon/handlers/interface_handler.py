from daemon.utils.interface import create_interface, delete_interface, list_interfaces

def handle_create(**kwargs):
    return create_interface(**kwargs)

def handle_delete(ifname: str):
    return delete_interface(ifname)

def handle_list(detailed: bool = True):
    return list_interfaces(detailed)
