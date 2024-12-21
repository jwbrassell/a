from app import create_app
from app.extensions import db
from app.models.role import Role
from app.models.permission import Permission
import sys
from datetime import datetime

def init_aws_permissions():
    """Initialize AWS manager permissions"""
    try:
        print("Initializing AWS manager permissions...")
        permissions = [
            {
                'name': 'aws_access',
                'description': 'Access AWS manager',
                'category': 'aws'
            },
            {
                'name': 'aws_create_config',
                'description': 'Create AWS configurations',
                'category': 'aws'
            },
            {
                'name': 'aws_delete_config',
                'description': 'Delete AWS configurations',
                'category': 'aws'
            },
            {
                'name': 'aws_manage_ec2',
                'description': 'Manage EC2 instances',
                'category': 'aws'
            },
            {
                'name': 'aws_manage_iam',
                'description': 'Manage IAM users',
                'category': 'aws'
            },
            {
                'name': 'aws_manage_security',
                'description': 'Manage security groups',
                'category': 'aws'
            },
            {
                'name': 'aws_manage_templates',
                'description': 'Manage EC2 templates',
                'category': 'aws'
            }
        ]

        for perm_data in permissions:
            perm = Permission.query.filter_by(name=perm_data['name']).first()
            if not perm:
                Permission.create_permission(
                    name=perm_data['name'],
                    description=perm_data['description'],
                    category=perm_data['category'],
                    created_by='system'
                )
        
        print("AWS permissions initialized successfully")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error initializing AWS permissions: {e}", file=sys.stderr)
        return False

def init_aws_roles():
    """Initialize AWS manager roles"""
    try:
        print("Initializing AWS manager roles...")
        # Common role attributes
        now = datetime.utcnow()
        base_attrs = {
            'created_by': 'system',
            'updated_by': 'system',
            'created_at': now,
            'updated_at': now,
            'is_system_role': True,
            'icon': 'fas fa-aws',
            'ldap_groups': [],
            'auto_sync': False
        }

        # AWS Administrator role
        admin_role = Role.query.filter_by(name='aws_administrator').first()
        if not admin_role:
            admin_role = Role(
                name='aws_administrator',
                description='Full access to AWS manager',
                weight=100,
                **base_attrs
            )
            # Add all AWS permissions
            aws_perms = Permission.query.filter(
                Permission.name.like('aws_%')
            ).all()
            for perm in aws_perms:
                admin_role.permissions.append(perm)
            db.session.add(admin_role)

        # AWS Operator role
        operator_role = Role.query.filter_by(name='aws_operator').first()
        if not operator_role:
            operator_role = Role(
                name='aws_operator',
                description='Can manage EC2 instances and view resources',
                weight=50,
                **base_attrs
            )
            # Add specific permissions
            operator_perms = ['aws_access', 'aws_manage_ec2']
            for perm_name in operator_perms:
                perm = Permission.query.filter_by(name=perm_name).first()
                if perm:
                    operator_role.permissions.append(perm)
            db.session.add(operator_role)

        # AWS Viewer role
        viewer_role = Role.query.filter_by(name='aws_viewer').first()
        if not viewer_role:
            viewer_role = Role(
                name='aws_viewer',
                description='Can view AWS resources',
                weight=10,
                **base_attrs
            )
            # Add view permission
            view_perm = Permission.query.filter_by(name='aws_access').first()
            if view_perm:
                viewer_role.permissions.append(view_perm)
            db.session.add(viewer_role)

        db.session.commit()
        print("AWS roles initialized successfully")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error initializing AWS roles: {e}", file=sys.stderr)
        return False

def verify_aws_setup():
    """Verify AWS manager database setup"""
    try:
        print("Verifying AWS manager setup...")
        # Check permissions
        required_perms = ['aws_access', 'aws_create_config', 'aws_delete_config',
                         'aws_manage_ec2', 'aws_manage_iam', 'aws_manage_security',
                         'aws_manage_templates']
        missing_perms = []
        for perm_name in required_perms:
            if not Permission.query.filter_by(name=perm_name).first():
                missing_perms.append(perm_name)
        
        if missing_perms:
            print(f"Missing permissions: {', '.join(missing_perms)}", file=sys.stderr)
            return False

        # Check roles
        required_roles = ['aws_administrator', 'aws_operator', 'aws_viewer']
        missing_roles = []
        for role_name in required_roles:
            if not Role.query.filter_by(name=role_name).first():
                missing_roles.append(role_name)
        
        if missing_roles:
            print(f"Missing roles: {', '.join(missing_roles)}", file=sys.stderr)
            return False

        print("AWS manager setup verified successfully")
        return True
    except Exception as e:
        print(f"Error verifying AWS setup: {e}", file=sys.stderr)
        return False

def init_database():
    """Initialize database with required data"""
    try:
        app = create_app()
        with app.app_context():
            print("Creating database tables...")
            db.create_all()

            # Initialize AWS manager
            if not init_aws_permissions():
                raise Exception("Failed to initialize AWS permissions")
            
            if not init_aws_roles():
                raise Exception("Failed to initialize AWS roles")
            
            if not verify_aws_setup():
                raise Exception("AWS manager setup verification failed")

            print("Database initialization completed successfully")
            return True
    except Exception as e:
        print(f"Error initializing database: {e}", file=sys.stderr)
        if app and app.debug:
            import traceback
            print(traceback.format_exc(), file=sys.stderr)
        return False

def main():
    """Main entry point with error handling"""
    try:
        if init_database():
            sys.exit(0)
        else:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nInitialization interrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
