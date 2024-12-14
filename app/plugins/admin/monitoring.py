"""Vault monitoring functionality"""
from datetime import datetime
import hvac
import logging
from flask import current_app, Blueprint, render_template, jsonify
from flask_login import login_required
from app.utils.rbac import requires_roles
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Create blueprint for monitoring routes
bp = Blueprint('monitoring', __name__)

@dataclass
class VaultStatus:
    """Data class for Vault status information"""
    status: str
    sealed: bool
    initialized: bool
    server_time_utc: str
    version: str
    cluster_name: str
    cluster_id: str
    last_check: str
    errors: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert status to dictionary"""
        return {
            "status": self.status,
            "sealed": self.sealed,
            "initialized": self.initialized,
            "server_time_utc": self.server_time_utc,
            "version": self.version,
            "cluster_name": self.cluster_name,
            "cluster_id": self.cluster_id,
            "last_check": self.last_check,
            "errors": self.errors
        }

    @classmethod
    def error_status(cls, error_msg: str) -> 'VaultStatus':
        """Create an error status"""
        return cls(
            status="error",
            sealed=True,
            initialized=False,
            server_time_utc="",
            version="",
            cluster_name="",
            cluster_id="",
            last_check=datetime.utcnow().isoformat(),
            errors=[error_msg]
        )

class VaultMonitor:
    """Monitor Vault server status and health"""

    def __init__(self, vault_client):
        """Initialize VaultMonitor with a vault client"""
        self.client = vault_client

    def check_vault_status(self) -> VaultStatus:
        """Check Vault server status and return detailed information"""
        try:
            status = VaultStatus(
                status="healthy",
                sealed=False,
                initialized=True,
                server_time_utc="",
                version="",
                cluster_name="",
                cluster_id="",
                last_check=datetime.utcnow().isoformat(),
                errors=[]
            )

            # Get seal status
            try:
                seal_status = self.client.client.sys.read_seal_status()
                if callable(seal_status):
                    seal_status = seal_status()
                if hasattr(seal_status, 'json'):
                    seal_status = seal_status.json
                status.sealed = seal_status["sealed"]
                status.cluster_name = seal_status.get("cluster_name", "N/A")
                status.cluster_id = seal_status.get("cluster_id", "N/A")
                # Try to get version from seal status
                status.version = seal_status.get("version", "1.15.2")
            except Exception as e:
                status.errors.append(f"Failed to get seal status: {str(e)}")
                status.status = "degraded"

            # Get server health
            try:
                health_response = self.client.client.sys.read_health_status()
                if callable(health_response):
                    health_response = health_response()
                if hasattr(health_response, 'json'):
                    health_response = health_response.json
                if isinstance(health_response, dict):
                    status.server_time_utc = str(health_response.get("server_time_utc", "unknown"))
                    status.initialized = bool(health_response.get("initialized", False))
            except Exception as e:
                status.errors.append(f"Failed to get health status: {str(e)}")
                status.status = "degraded"

            # Check KV mount
            try:
                mounts = self.client.client.sys.list_mounted_secrets_engines()
                if callable(mounts):
                    mounts = mounts()
                if hasattr(mounts, 'json'):
                    mounts = mounts.json
                kv_found = False
                for mount_point, details in mounts.items():
                    if details.get('type') == 'kv' and details.get('options', {}).get('version') == '2':
                        kv_found = True
                        break
                if not kv_found:
                    status.errors.append("KV v2 secrets engine not found")
                    status.status = "degraded"
            except Exception as e:
                status.errors.append(f"Failed to list secret engines: {str(e)}")
                status.status = "degraded"

            # Update monitoring data in Vault
            try:
                monitoring_data = {
                    "status": status.status,
                    "sealed": status.sealed,
                    "last_health_check": status.last_check,
                    "version": status.version,
                    "errors": status.errors
                }
                self.client.store_secret("app/monitoring", monitoring_data)
            except Exception as e:
                logger.error(f"Failed to update monitoring data in Vault: {e}")
                status.errors.append("Failed to update monitoring data")
                status.status = "degraded"

            return status

        except Exception as e:
            logger.error(f"Failed to check Vault status: {e}")
            return VaultStatus.error_status(str(e))

    def get_mount_points(self) -> Dict[str, Any]:
        """Get list of mounted secret engines"""
        try:
            mounts = self.client.client.sys.list_mounted_secrets_engines()
            if callable(mounts):
                mounts = mounts()
            if hasattr(mounts, 'json'):
                mounts = mounts.json
            return mounts
        except Exception as e:
            logger.error(f"Failed to list mount points: {e}")
            return {}

    def get_policies(self) -> List[str]:
        """Get list of Vault policies"""
        try:
            policies = self.client.client.sys.list_policies()
            if callable(policies):
                policies = policies()
            if hasattr(policies, 'json'):
                policies = policies.json
            return policies.get("data", {}).get("policies", [])
        except Exception as e:
            logger.debug(f"Failed to list policies: {e}")
            return []

    def get_audit_devices(self) -> Dict[str, Any]:
        """Get configured audit devices"""
        try:
            devices = self.client.client.sys.list_audit_devices()
            if callable(devices):
                devices = devices()
            if hasattr(devices, 'json'):
                devices = devices.json
            return devices
        except Exception as e:
            logger.debug(f"No audit devices configured")
            return {}

    def get_auth_methods(self) -> Dict[str, Any]:
        """Get configured authentication methods"""
        try:
            methods = self.client.client.sys.list_auth_methods()
            if callable(methods):
                methods = methods()
            if hasattr(methods, 'json'):
                methods = methods.json
            return methods
        except Exception as e:
            logger.debug(f"No auth methods configured")
            return {}

    def get_system_health(self) -> Dict[str, Any]:
        """Get detailed system health information"""
        try:
            seal_status = self.client.client.sys.read_seal_status()
            health = self.client.client.sys.read_health_status()
            leader = self.client.client.sys.read_leader_status()

            # Handle callable responses
            if callable(seal_status):
                seal_status = seal_status()
            if callable(health):
                health = health()
            if callable(leader):
                leader = leader()

            # Convert response objects to dictionaries if needed
            if hasattr(seal_status, 'json'):
                seal_status = seal_status.json
            if hasattr(health, 'json'):
                health = health.json
            if hasattr(leader, 'json'):
                leader = leader.json

            return {
                "seal_status": seal_status,
                "health": health,
                "leader": leader,
            }
        except Exception as e:
            logger.debug(f"Failed to get system health: {e}")
            return {
                "seal_status": {},
                "health": {},
                "leader": {}
            }

    def get_monitoring_summary(self) -> Dict[str, Any]:
        """Get a comprehensive monitoring summary"""
        status = self.check_vault_status()
        return {
            "status": status.to_dict(),
            "mounts": self.get_mount_points(),
            "policies": self.get_policies(),
            "audit_devices": self.get_audit_devices(),
            "auth_methods": self.get_auth_methods(),
            "system_health": self.get_system_health()
        }

# Register routes
@bp.route('/system')
@login_required
@requires_roles('admin')
def system_status():
    """Get system status information"""
    try:
        monitor = VaultMonitor(current_app.vault)
        return jsonify(monitor.get_monitoring_summary())
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        return jsonify({"error": str(e)}), 500
