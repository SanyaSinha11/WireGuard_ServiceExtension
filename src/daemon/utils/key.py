import shutil
import subprocess
from typing import Dict, Any

def generate_keypair() -> Dict[str, Any]:
    """Generate WireGuard private/public key pair."""
    if not shutil.which("wg"):
        return {"status": "error", "message": "wg binary required to generate keys."}
    try:
        priv = subprocess.check_output(["wg", "genkey"], text=True).strip()
        pub = subprocess.run(["wg", "pubkey"], input=priv, capture_output=True, text=True).stdout.strip()
        return {"status": "success", "private_key": priv, "public_key": pub}
    except Exception as e:
        return {"status": "error", "message": f"keygen error: {e}"}
