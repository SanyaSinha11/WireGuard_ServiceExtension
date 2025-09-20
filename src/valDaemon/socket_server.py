import os
import json
import socket
import threading
import signal
import sys

from valDaemon.handlers.interface_handler import handle_create, handle_delete, handle_list
from valDaemon.handlers.peer_handler import handle_list as peers_list, handle_add, handle_remove
from valDaemon.handlers.key_handler import handle_gen_keys

DEFAULT_SOCKET = "/run/valdaemon.sock"
FALLBACK_SOCKET = "/tmp/valdaemon.sock"

class SocketDaemon:
    def __init__(self, socket_path=None):
        self.socket_path = socket_path or (DEFAULT_SOCKET if os.geteuid() == 0 else FALLBACK_SOCKET)
        self.server = None
        self.running = False

    def start(self):
        # remove stale socket
        try:
            if os.path.exists(self.socket_path):
                os.remove(self.socket_path)
        except Exception:
            pass

        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(self.socket_path)
        try:
            os.chmod(self.socket_path, 0o660)
        except Exception:
            pass

        server.listen(5)
        self.server = server
        self.running = True
        print(f"[valDaemon] Listening on {self.socket_path} (pid {os.getpid()})")
        try:
            while self.running:
                try:
                    conn, _ = server.accept()
                except KeyboardInterrupt:
                    break
                threading.Thread(target=self.handle_conn, args=(conn,), daemon=True).start()
        finally:
            self.shutdown()

    def handle_conn(self, conn: socket.socket):
        try:
            raw = b""
            while True:
                chunk = conn.recv(65536)
                if not chunk:
                    break
                raw += chunk
            if not raw:
                conn.send(b'{"status":"error","message":"empty request"}')
                conn.close()
                return
            try:
                payload = json.loads(raw.decode("utf-8"))
            except Exception as e:
                conn.send(json.dumps({"status":"error","message":f"invalid json: {e}"}).encode("utf-8"))
                conn.close()
                return

            action = payload.get("action")
            out = {"status":"error", "message":"unknown action"}
            if action == "create_interface":
                out = handle_create(payload.get("interface","wg0"))
            elif action == "delete_interface":
                out = handle_delete(payload.get("interface","wg0"))
            elif action == "list_interfaces":
                out = handle_list()
            elif action == "list_peers":
                out = peers_list(payload.get("interface","wg0"))
            elif action == "add_peer":
                if not payload.get("public_key") or not payload.get("allowed_ips"):
                    out = {"status":"error","message":"public_key and allowed_ips required"}
                else:
                    out = handle_add(payload.get("interface","wg0"),
                                     payload.get("public_key"),
                                     payload.get("allowed_ips"))
            elif action == "remove_peer":
                if not payload.get("public_key"):
                    out = {"status":"error","message":"public_key required"}
                else:
                    out = handle_remove(payload.get("interface","wg0"), payload.get("public_key"))
            elif action == "generate_keypair":
                out = handle_gen_keys()
            else:
                out = {"status":"error", "message": f"unknown action: {action}"}

            conn.send(json.dumps(out).encode("utf-8"))
        except Exception as e:
            try:
                conn.send(json.dumps({"status":"error","message":f"server error: {e}"}).encode("utf-8"))
            except Exception:
                pass
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def shutdown(self):
        self.running = False
        try:
            if self.server:
                self.server.close()
        except Exception:
            pass
        try:
            if os.path.exists(self.socket_path):
                os.remove(self.socket_path)
        except Exception:
            pass

def run(socket_path=None):
    daemon = SocketDaemon(socket_path)
    def _handle(sig, frame):
        print("Signal received, shutting down...")
        daemon.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, _handle)
    signal.signal(signal.SIGTERM, _handle)
    daemon.start()

if __name__ == "__main__":
    run()