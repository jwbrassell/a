#!/usr/bin/env python3
import os
import signal
import sys
from pathlib import Path

def shutdown_vault():
    """Gracefully shut down the Vault server."""
    pid_file = Path("vault.pid")
    
    try:
        # Check if PID file exists
        if not pid_file.exists():
            print("Vault PID file not found. Is Vault running?")
            return
        
        # Read PID
        pid = int(pid_file.read_text().strip())
        
        # Send SIGTERM signal
        print(f"Sending shutdown signal to Vault process (PID: {pid})...")
        os.kill(pid, signal.SIGTERM)
        
        # Remove PID file
        pid_file.unlink()
        
        print("Vault server has been shut down.")
        
    except ProcessLookupError:
        print("Vault process not found. Cleaning up PID file...")
        pid_file.unlink()
    except ValueError:
        print("Invalid PID in vault.pid file")
    except Exception as e:
        print(f"Error shutting down Vault: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    shutdown_vault()
