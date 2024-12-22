"""Permissions management package."""
from .manager import PermissionsManager
from .admin import ADMIN_PERMISSIONS
from .aws import AWS_PERMISSIONS
from .handoffs import HANDOFF_PERMISSIONS
from .dispatch import DISPATCH_PERMISSIONS
from .database_reports import DATABASE_REPORTS_PERMISSIONS
from .documents import DOCUMENT_PERMISSIONS
from .oncall import ONCALL_PERMISSIONS

__all__ = [
    'PermissionsManager',
    'ADMIN_PERMISSIONS',
    'AWS_PERMISSIONS',
    'HANDOFF_PERMISSIONS',
    'DISPATCH_PERMISSIONS',
    'DATABASE_REPORTS_PERMISSIONS',
    'DOCUMENT_PERMISSIONS',
    'ONCALL_PERMISSIONS',
]
