from valDaemon.utils.wg_service import create_interface, delete_interface, list_interfaces

def handle_create(interface_name: str = "wg0"):
    return create_interface(interface_name)

def handle_delete(interface_name: str = "wg0"):
    return delete_interface(interface_name)

def handle_list():
    return list_interfaces()
