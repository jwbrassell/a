"""Add plugin-specific permissions

Revision ID: add_plugin_permissions
Revises: init_rbac_data
Create Date: 2024-01-02 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime
from sqlalchemy.orm import Session

# revision identifiers, used by Alembic.
revision = 'add_plugin_permissions'
down_revision = 'init_rbac_data'
branch_labels = None
depends_on = None

def upgrade():
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
        
        # Define plugin permissions
        plugin_permissions = {
            'admin': [
                ('admin_access', 'Access admin interface', ['read']),
                ('admin_manage', 'Manage admin settings', ['write'])
            ],
            'awsmon': [
                ('awsmon_view', 'View AWS monitoring', ['read']),
                ('awsmon_manage', 'Manage AWS monitoring', ['write'])
            ],
            'dispatch': [
                ('dispatch_view', 'View dispatch items', ['read']),
                ('dispatch_manage', 'Manage dispatch items', ['write'])
            ],
            'documents': [
                ('documents_view', 'View documents', ['read']),
                ('documents_manage', 'Manage documents', ['write']),
                ('documents_delete', 'Delete documents', ['delete'])
            ],
            'handoffs': [
                ('handoffs_view', 'View handoffs', ['read']),
                ('handoffs_manage', 'Manage handoffs', ['write'])
            ],
            'oncall': [
                ('oncall_view', 'View on-call schedule', ['read']),
                ('oncall_manage', 'Manage on-call schedule', ['write'])
            ],
            'reports': [
                ('reports_view', 'View reports', ['read']),
                ('reports_manage', 'Manage reports', ['write']),
                ('reports_export', 'Export reports', ['read'])
            ],
            'weblinks': [
                ('weblinks_access', 'View and search web links', ['read']),
                ('weblinks_manage', 'Manage web links, categories, and tags', ['write']),
                ('weblinks_import_export', 'Import and export web links', ['read', 'write'])
            ]
        }
        
        # Add permissions for each plugin
        for plugin, permissions in plugin_permissions.items():
            for perm_name, description, actions_needed in permissions:
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
                    action_id = action_map.get((action_name, 'GET' if action_name == 'read' else 'POST'))
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
        raise Exception(f"Error adding plugin permissions: {str(e)}")
    
    finally:
        session.close()

def downgrade():
    bind = op.get_bind()
    session = Session(bind=bind)
    
    try:
        # Get all plugin permission names
        plugin_permissions = [
            'admin_access', 'admin_manage',
            'awsmon_view', 'awsmon_manage',
            'dispatch_view', 'dispatch_manage',
            'documents_view', 'documents_manage', 'documents_delete',
            'handoffs_view', 'handoffs_manage',
            'oncall_view', 'oncall_manage',
            'reports_view', 'reports_manage', 'reports_export',
            'weblinks_access', 'weblinks_manage', 'weblinks_import_export'
        ]
        
        # Get permission IDs
        permission_ids = session.execute(
            sa.text('SELECT id FROM permission WHERE name IN :names'),
            {'names': tuple(plugin_permissions)}
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
        raise Exception(f"Error removing plugin permissions: {str(e)}")
    
    finally:
        session.close()
