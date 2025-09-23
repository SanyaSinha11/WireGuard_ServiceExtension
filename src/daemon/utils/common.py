import subprocess
from typing import List, Dict, Any

def run_cmd(cmd: List[str]) -> Dict[str, Any]:
    """Run a system command with error handling."""
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
    except Exception as e:
        return {"status": "error", "message": f"Failed to run {cmd}: {e}"}

    if proc.returncode != 0:
        return {
            "status": "error",
            "message": f"Command failed: {' '.join(cmd)}",
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
            "rc": proc.returncode
        }
    return {"status": "success", "stdout": proc.stdout.strip(), "stderr": proc.stderr.strip(), "rc": proc.returncode}
