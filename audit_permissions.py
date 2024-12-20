#!/usr/bin/env python3
"""
Permission audit script to analyze and verify permissions across the application.
This script helps identify:
1. Unused permissions
2. Missing actions
3. Duplicate permissions
4. Inconsistent naming
5. Permission usage statistics
"""
import os
import sys
import logging
from app import create_app
from app.utils.permissions import PermissionsManager
from app.models.permission import Permission
from app.models.role import Role

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")

def audit_permissions():
    """Run a comprehensive permission audit."""
    app = create_app()
    with app.app_context():
        print_section("Permission Audit Report")
        
        # Get audit results
        audit_results = PermissionsManager.audit_permissions()
        
        # Print unused permissions
        print("Unused Permissions:")
        if audit_results['unused_permissions']:
            for perm in audit_results['unused_permissions']:
                print(f"  - {perm}")
        else:
            print("  None found")
        
        # Print permissions missing actions
        print("\nPermissions Missing Actions:")
        if audit_results['missing_actions']:
            for perm in audit_results['missing_actions']:
                print(f"  - {perm}")
        else:
            print("  None found")
        
        # Print duplicate permissions
        print("\nDuplicate Permissions:")
        if audit_results['duplicate_permissions']:
            for perm in audit_results['duplicate_permissions']:
                print(f"  - {perm}")
        else:
            print("  None found")
        
        # Print inconsistent naming
        print("\nInconsistent Naming:")
        if audit_results['inconsistent_naming']:
            for perm in audit_results['inconsistent_naming']:
                print(f"  - {perm}")
        else:
            print("  None found")
        
        print_section("Permission Usage Statistics")
        
        # Get usage statistics
        usage_stats = PermissionsManager.get_permission_usage()
        
        # Sort by usage count
        sorted_stats = sorted(usage_stats.items(), key=lambda x: x[1], reverse=True)
        
        print("Permission Usage (by number of roles):")
        for perm, count in sorted_stats:
            print(f"  {perm}: {count} roles")
        
        print_section("Role Analysis")
        
        # Analyze roles and their permissions
        roles = Role.query.all()
        print(f"Total Roles: {len(roles)}")
        
        for role in roles:
            print(f"\nRole: {role.name}")
            print(f"  Description: {role.description}")
            print(f"  Permission Count: {len(role.permissions)}")
            print("  Permissions:")
            for perm in role.permissions:
                print(f"    - {perm.name}")
        
        print_section("Module Coverage")
        
        # Check module coverage
        all_permissions = Permission.query.all()
        modules = {p.name.split('_')[0] for p in all_permissions}
        
        print("Permission coverage by module:")
        for module in sorted(modules):
            module_perms = [p for p in all_permissions if p.name.startswith(f"{module}_")]
            print(f"\n{module.upper()}:")
            print(f"  Total Permissions: {len(module_perms)}")
            print("  Permissions:")
            for perm in module_perms:
                print(f"    - {perm.name}")
                print(f"      Description: {perm.description}")
                print(f"      Actions: {', '.join(a.name for a in perm.actions)}")

def main():
    """Main function."""
    try:
        audit_permissions()
    except Exception as e:
        logger.error(f"Audit failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
