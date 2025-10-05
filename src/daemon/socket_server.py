import os
import json
import socket
import threading
import signal
import sys
from concurrent.futures import ThreadPoolExecutor

from daemon.handlers.interface_handler import handle_create, handle_delete, handle_list, handle_restart
from daemon.handlers.peer_handler import handle_list as peers_list, handle_add, handle_remove
from daemon.handlers.key_handler import handle_gen_keys

DEFAULT_SOCKET = "/run/wg.daemon.sock"
FALLBACK_SOCKET = "/tmp/wg.daemon.sock"


class SocketDaemon:
    def __init__(self, socket_path=None, max_workers=10, permissive_for_nonroot=False):
        self.socket_path = socket_path or (DEFAULT_SOCKET if os.geteuid() == 0 else FALLBACK_SOCKET)
        self.server = None
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.permissive_for_nonroot = permissive_for_nonroot

    def confirm_ready(self):
        """Confirm the daemon is built successfully by checking socket availability."""
        if self.server and os.path.exists(self.socket_path):
            print(f"[daemon] Build successful – socket ready at {self.socket_path}")
            return True
        print("[daemon] Build failed – socket not available")
        return False

    def start(self):
        try:
            if os.path.exists(self.socket_path):
                os.remove(self.socket_path)
        except Exception:
            pass

        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            server.bind(self.socket_path)
        except Exception as e:
            print(f"[daemon] bind failed: {e}")
            raise

        try:
            if os.geteuid() == 0:
                mode = 0o660
            else:
                mode = 0o666 if self.permissive_for_nonroot else 0o600
            os.chmod(self.socket_path, mode)
        except Exception as e:
            print(f"[daemon] chmod failed: {e}")

        server.listen(5)
        self.server = server
        self.running = True
        print(f"[daemon] Listening on {self.socket_path} (pid {os.getpid()})")

        # confirm daemon is ready
        self.confirm_ready()

        try:
            while self.running:
                try:
                    conn, _ = server.accept()
                except OSError:
                    break
                self.executor.submit(self.handle_conn, conn)
        finally:
            self.shutdown()

    def handle_conn(self, conn: socket.socket):
        try:
            conn.settimeout(5.0)
            buffer = b""
            while True:
                try:
                    chunk = conn.recv(65536)
                except socket.timeout:
                    if not buffer:
                        break
                    chunk = b""
                if not chunk:
                    break
                buffer += chunk
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    if not line.strip():
                        try:
                            conn.sendall(b'{"status":"error","message":"empty request"}\n')
                        except Exception:
                            pass
                        continue

                    try:
                        payload = json.loads(line.decode("utf-8"))
                    except Exception as e:
                        try:
                            conn.sendall(
                                (json.dumps({"status": "error", "message": f"invalid json: {e}"}) + "\n").encode("utf-8")
                            )
                        except Exception:
                            pass
                        continue

                    # Connection test
                    if payload.get("action") == "ping":
                        try:
                            conn.sendall(b'{"status":"success","message":"pong"}\n')
                        except Exception:
                            return
                        continue

                    out = self._dispatch(payload)
                    try:
                        conn.sendall((json.dumps(out) + "\n").encode("utf-8"))
                    except Exception:
                        return

            if buffer.strip():
                try:
                    payload = json.loads(buffer.decode("utf-8").strip())
                    if payload.get("action") == "ping":
                        conn.sendall(b'{"status":"success","message":"pong"}\n')
                    else:
                        out = self._dispatch(payload)
                        conn.sendall((json.dumps(out) + "\n").encode("utf-8"))
                except Exception:
                    try:
                        conn.sendall(
                            (json.dumps({"status": "error", "message": "invalid or incomplete json (no newline)"}) + "\n").encode(
                                "utf-8"
                            )
                        )
                    except Exception:
                        pass

        except Exception as e:
            try:
                conn.sendall((json.dumps({"status": "error", "message": f"server error: {e}"}) + "\n").encode("utf-8"))
            except Exception:
                pass
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def _dispatch(self, payload: dict):
        action = payload.get("action")
        try:
            if action == "create_interface":
                return handle_create(payload.get("interface", "wg0"))
            elif action == "delete_interface":
                return handle_delete(payload.get("interface", "wg0"))
            elif action == "restart_interface":
                return handle_restart(payload.get("interface", "wg0"))
            elif action == "list_interfaces":
                return handle_list()
            elif action == "list_peers":
                return peers_list(payload.get("interface", "wg0"))
            elif action == "add_peer":
                if not payload.get("public_key") or not payload.get("allowed_ips"):
                    return {"status": "error", "message": "public_key and allowed_ips required"}
                return handle_add(
                    ifname=payload.get("interface", "wg0"),
                    public_key=payload.get("public_key"),
                    allowed_ips=payload.get("allowed_ips"),
                    preshared_key=payload.get("preshared_key"),
                    endpoint=payload.get("endpoint"),
                    persistent_keepalive=payload.get("persistent_keepalive"),
                )
            elif action == "remove_peer":
                if not payload.get("public_key"):
                    return {"status": "error", "message": "public_key required"}
                return handle_remove(payload.get("interface", "wg0"), payload.get("public_key"))
            elif action == "generate_keypair":
                return handle_gen_keys()
            else:
                return {"status": "error", "message": f"unknown action: {action}"}
        except Exception as e:
            return {"status": "error", "message": f"handler error: {e}"}

    def shutdown(self):
        if not self.running:
            return
        self.running = False
        try:
            if self.server:
                try:
                    self.server.shutdown(socket.SHUT_RDWR)
                except Exception:
                    pass
                try:
                    self.server.close()
                except Exception:
                    pass
                self.server = None
        except Exception:
            pass

        try:
            if os.path.exists(self.socket_path):
                os.remove(self.socket_path)
        except Exception:
            pass

        try:
            self.executor.shutdown(wait=False)
        except Exception:
            pass


def run(socket_path=None, permissive_for_nonroot=False):
    daemon = SocketDaemon(socket_path, permissive_for_nonroot=permissive_for_nonroot)

    def _handle(sig, frame):
        print("Signal received, shutting down...")
        daemon.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, _handle)
    signal.signal(signal.SIGTERM, _handle)
    daemon.start()


if __name__ == "__main__":
    run()