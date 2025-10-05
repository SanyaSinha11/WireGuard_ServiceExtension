from daemon.utils.interface import create_interface, delete_interface, list_interfaces, restart_interface

def handle_create(**kwargs):   # def handle_create(ifname: str):
    return create_interface(**kwargs)  #   return create_interface(ifname) 

def handle_delete(ifname: str):
    return delete_interface(ifname)

def handle_list(detailed: bool = True):
    return list_interfaces(detailed)

def handle_restart(ifname: str):
    return restart_interface(ifname)
