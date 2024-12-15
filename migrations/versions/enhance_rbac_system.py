"""Enhance RBAC system with permissions and role improvements.

Revision ID: enhance_rbac_system
Revises: # Leave this empty, alembic will fill it
Create Date: 2024-01-01 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic
revision = 'enhance_rbac_system'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add new columns to role table
    op.add_column('role', sa.Column('notes', sa.Text(), nullable=True))
    op.add_column('role', sa.Column('icon', sa.String(50), nullable=False, server_default='fas fa-user-tag'))
    op.add_column('role', sa.Column('is_system_role', sa.Boolean(), nullable=False, server_default='0'))
    op.add_column('role', sa.Column('weight', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('role', sa.Column('updated_by', sa.String(64), nullable=True))

    # Create permission table
    op.create_table(
        'permission',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('description', sa.String(256), nullable=True),
        sa.Column('category', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('created_by', sa.String(64), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('updated_by', sa.String(64), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create role_permissions association table
    op.create_table(
        'role_permissions',
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['role.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['permission_id'], ['permission.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('role_id', 'permission_id')
    )

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
        connection.execute(
            sa.text(
                'INSERT INTO permission (name, description, category, created_at, created_by) '
                'VALUES (:name, :description, :category, :created_at, :created_by)'
            ),
            {
                'name': name,
                'description': description,
                'category': category,
                'created_at': datetime.utcnow(),
                'created_by': 'system'
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

    # Add all permissions to admin role
    connection.execute(
        sa.text(
            'INSERT INTO role_permissions (role_id, permission_id) '
            'SELECT r.id, p.id FROM role r, permission p '
            'WHERE r.name = :role_name'
        ),
        {'role_name': 'admin'}
    )

def downgrade():
    # Remove indexes
    op.drop_index('ix_role_weight')
    op.drop_index('ix_role_is_system_role')
    op.drop_index('ix_permission_name')
    op.drop_index('ix_permission_category')

    # Drop tables
    op.drop_table('role_permissions')
    op.drop_table('permission')

    # Remove columns from role table
    op.drop_column('role', 'updated_by')
    op.drop_column('role', 'weight')
    op.drop_column('role', 'is_system_role')
    op.drop_column('role', 'icon')
    op.drop_column('role', 'notes')
