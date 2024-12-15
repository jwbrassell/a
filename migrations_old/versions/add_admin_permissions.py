"""Add admin permissions

Revision ID: add_admin_permissions
Revises: init_enhanced_rbac_data
Create Date: 2024-01-02 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'add_admin_permissions'
down_revision = 'init_enhanced_rbac_data'
branch_labels = None
depends_on = None

def upgrade():
    # Create session
    bind = op.get_bind()
    session = Session(bind=bind)
    
    try:
        # Get admin role
        admin_role = session.execute(
            sa.text('SELECT id FROM role WHERE name = :name'),
            {'name': 'admin'}
        ).fetchone()
        
        if not admin_role:
            raise Exception("Admin role not found")
        
        # Get actions
        actions = session.execute(
            sa.text('SELECT id, name, method FROM action')
        ).fetchall()
        action_map = {(a.name, a.method): a.id for a in actions}
        
        # Define admin permissions
        admin_permissions = [
            ('admin_dashboard_access', 'Dashboard access', ['read']),
            ('admin_vault_access', 'Vault management access', ['read']),
            ('admin_monitoring_access', 'System monitoring access', ['read']),
            ('admin_users_access', 'User management access', ['read', 'write']),
            ('admin_roles_access', 'Role management access', ['read', 'write', 'update', 'delete']),
            ('admin_categories_access', 'Category management access', ['read', 'write', 'update', 'delete']),
            ('admin_routes_access', 'Route management access', ['read', 'write', 'update', 'delete']),
            ('admin_logs_access', 'System logs access', ['read']),
            ('admin_icons_access', 'Icon management access', ['read'])
        ]
        
        # Add permissions
        for perm_name, description, actions_needed in admin_permissions:
            # Create permission
            session.execute(
                sa.text(
                    'INSERT INTO permission (name, description, created_by, created_at, updated_at) '
                    'VALUES (:name, :description, :created_by, :created_at, :updated_at)'
                ),
                {
                    'name': perm_name,
                    'description': description,
                    'created_by': 'system',
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                }
            )
            
            # Get the permission ID
            perm_id = session.execute(
                sa.text('SELECT id FROM permission WHERE name = :name'),
                {'name': perm_name}
            ).fetchone()[0]
            
            # Associate actions with permission
            for action_name in actions_needed:
                action_id = action_map.get((action_name, 'GET' if action_name == 'read' else 
                                          'POST' if action_name == 'write' else
                                          'PUT' if action_name == 'update' else
                                          'DELETE'))
                if action_id:
                    session.execute(
                        sa.text(
                            'INSERT INTO permission_actions (permission_id, action_id) '
                            'VALUES (:permission_id, :action_id)'
                        ),
                        {
                            'permission_id': perm_id,
                            'action_id': action_id
                        }
                    )
            
            # Associate permission with admin role
            session.execute(
                sa.text(
                    'INSERT INTO role_permissions (role_id, permission_id) '
                    'VALUES (:role_id, :permission_id)'
                ),
                {
                    'role_id': admin_role[0],
                    'permission_id': perm_id
                }
            )
        
        session.commit()
        
    except Exception as e:
        session.rollback()
        raise Exception(f"Error adding admin permissions: {str(e)}")
    
    finally:
        session.close()

def downgrade():
    # Create session
    bind = op.get_bind()
    session = Session(bind=bind)
    
    try:
        # Get permission IDs
        admin_permission_names = [
            'admin_dashboard_access',
            'admin_vault_access',
            'admin_monitoring_access',
            'admin_users_access',
            'admin_roles_access',
            'admin_categories_access',
            'admin_routes_access',
            'admin_logs_access',
            'admin_icons_access'
        ]
        
        # Get permission IDs
        permission_ids = session.execute(
            sa.text('SELECT id FROM permission WHERE name IN :names'),
            {'names': tuple(admin_permission_names)}
        ).fetchall()
        
        if permission_ids:
            perm_ids = [p[0] for p in permission_ids]
            
            # Remove role associations
            session.execute(
                sa.text('DELETE FROM role_permissions WHERE permission_id IN :ids'),
                {'ids': tuple(perm_ids)}
            )
            
            # Remove action associations
            session.execute(
                sa.text('DELETE FROM permission_actions WHERE permission_id IN :ids'),
                {'ids': tuple(perm_ids)}
            )
            
            # Remove permissions
            session.execute(
                sa.text('DELETE FROM permission WHERE id IN :ids'),
                {'ids': tuple(perm_ids)}
            )
        
        session.commit()
        
    except Exception as e:
        session.rollback()
        raise Exception(f"Error removing admin permissions: {str(e)}")
    
    finally:
        session.close()
