"""Enhance RBAC system with permissions and role improvements.

Revision ID: enhance_rbac_system
Revises: add_plugin_permissions
Create Date: 2024-01-01 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic
revision = 'enhance_rbac_system'
down_revision = 'add_plugin_permissions'
branch_labels = None
depends_on = None

def upgrade():
    # Add new columns to role table
    op.add_column('role', sa.Column('notes', sa.Text(), nullable=True))
    op.add_column('role', sa.Column('icon', sa.String(50), nullable=False, server_default='fas fa-user-tag'))
    op.add_column('role', sa.Column('is_system_role', sa.Boolean(), nullable=False, server_default='0'))
    op.add_column('role', sa.Column('weight', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('role', sa.Column('updated_by', sa.String(64), nullable=True))

    # Add new columns to permission table
    op.add_column('permission', sa.Column('category', sa.String(64), nullable=True))
    op.add_column('permission', sa.Column('updated_by', sa.String(64), nullable=True))

    # Create indexes
    op.create_index('ix_permission_category', 'permission', ['category'])
    op.create_index('ix_permission_name', 'permission', ['name'])
    op.create_index('ix_role_is_system_role', 'role', ['is_system_role'])
    op.create_index('ix_role_weight', 'role', ['weight'])

    # Initialize default permissions
    connection = op.get_bind()
    
    # Insert default permissions
    default_permissions = [
        # Admin permissions
        ('admin_dashboard_access', 'Access admin dashboard', 'admin'),
        ('admin_users_access', 'Access user management', 'admin'),
        ('admin_roles_access', 'Access role management', 'admin'),
        ('admin_monitoring_access', 'Access system monitoring', 'admin'),
        ('admin_logs_access', 'Access system logs', 'admin'),
        
        # User permissions
        ('user_profile_access', 'Access user profile', 'user'),
        ('user_settings_access', 'Access user settings', 'user'),
        
        # Content permissions
        ('content_create', 'Create content', 'content'),
        ('content_edit', 'Edit content', 'content'),
        ('content_delete', 'Delete content', 'content'),
        ('content_publish', 'Publish content', 'content'),
        
        # System permissions
        ('system_settings_access', 'Access system settings', 'system'),
        ('system_backup_access', 'Access backup functionality', 'system'),
        ('system_update_access', 'Access system updates', 'system')
    ]
    
    for name, description, category in default_permissions:
        # Check if permission already exists
        result = connection.execute(
            sa.text('SELECT id FROM permission WHERE name = :name'),
            {'name': name}
        ).fetchone()
        
        if not result:
            now = datetime.utcnow()
            connection.execute(
                sa.text(
                    'INSERT INTO permission (name, description, category, created_at, created_by, updated_at) '
                    'VALUES (:name, :description, :category, :created_at, :created_by, :updated_at)'
                ),
                {
                    'name': name,
                    'description': description,
                    'category': category,
                    'created_at': now,
                    'created_by': 'system',
                    'updated_at': now
                }
            )

    # Update existing admin role to be a system role
    connection.execute(
        sa.text(
            'UPDATE role SET is_system_role = 1, icon = :icon, notes = :notes '
            'WHERE name = :name'
        ),
        {
            'icon': 'fas fa-shield-alt',
            'notes': 'System administrator role with full access',
            'name': 'admin'
        }
    )

    # Add all permissions to admin role if not already added
    connection.execute(
        sa.text(
            'INSERT INTO role_permissions (role_id, permission_id) '
            'SELECT r.id, p.id FROM role r, permission p '
            'WHERE r.name = :role_name '
            'AND NOT EXISTS (SELECT 1 FROM role_permissions rp WHERE rp.role_id = r.id AND rp.permission_id = p.id)'
        ),
        {'role_name': 'admin'}
    )

def downgrade():
    # Remove indexes
    op.drop_index('ix_role_weight')
    op.drop_index('ix_role_is_system_role')
    op.drop_index('ix_permission_name')
    op.drop_index('ix_permission_category')

    # Remove columns from permission table
    op.drop_column('permission', 'updated_by')
    op.drop_column('permission', 'category')

    # Remove columns from role table
    op.drop_column('role', 'updated_by')
    op.drop_column('role', 'weight')
    op.drop_column('role', 'is_system_role')
    op.drop_column('role', 'icon')
    op.drop_column('role', 'notes')
