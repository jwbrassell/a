"""Add oncall permissions

Revision ID: add_oncall_permissions
Revises: add_handoffs_permissions
Create Date: 2024-01-02 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'add_oncall_permissions'
down_revision = 'add_handoffs_permissions'
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
        
        # Define oncall permissions
        oncall_permissions = [
            ('oncall_access', 'View on-call schedules and rotations', ['read']),
            ('oncall_manage', 'Manage on-call teams and upload schedules', ['read', 'write'])
        ]
        
        # Add permissions
        for perm_name, description, actions_needed in oncall_permissions:
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
        raise Exception(f"Error adding oncall permissions: {str(e)}")
    
    finally:
        session.close()

def downgrade():
    # Create session
    bind = op.get_bind()
    session = Session(bind=bind)
    
    try:
        # Get permission IDs
        oncall_permission_names = [
            'oncall_access',
            'oncall_manage'
        ]
        
        # Get permission IDs
        permission_ids = session.execute(
            sa.text('SELECT id FROM permission WHERE name IN :names'),
            {'names': tuple(oncall_permission_names)}
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
        raise Exception(f"Error removing oncall permissions: {str(e)}")
    
    finally:
        session.close()