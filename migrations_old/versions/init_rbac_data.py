"""Initialize RBAC data

Revision ID: init_rbac_data
Revises: initial_schema
Create Date: 2024-01-02 20:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime
from sqlalchemy.orm import Session

# revision identifiers, used by Alembic.
revision = 'init_rbac_data'
down_revision = 'initial_schema'
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    session = Session(bind=bind)
    
    try:
        # Create default actions
        actions = [
            ('read', 'GET', 'Read access'),
            ('write', 'POST', 'Write access'),
            ('update', 'PUT', 'Update access'),
            ('delete', 'DELETE', 'Delete access')
        ]
        
        for name, method, description in actions:
            session.execute(
                sa.text(
                    'INSERT INTO action (name, method, description, created_at, created_by) '
                    'VALUES (:name, :method, :description, :created_at, :created_by)'
                ),
                {
                    'name': name,
                    'method': method,
                    'description': description,
                    'created_at': datetime.utcnow(),
                    'created_by': 'system'
                }
            )
        
        # Create base roles
        roles = [
            ('admin', 'Administrator with full access'),
            ('user', 'Regular user with basic access'),
            ('manager', 'Manager with elevated access'),
            ('readonly', 'Read-only access user')
        ]
        
        for name, description in roles:
            session.execute(
                sa.text(
                    'INSERT INTO role (name, description, created_at, created_by, updated_at) '
                    'VALUES (:name, :description, :created_at, :created_by, :updated_at)'
                ),
                {
                    'name': name,
                    'description': description,
                    'created_at': datetime.utcnow(),
                    'created_by': 'system',
                    'updated_at': datetime.utcnow()
                }
            )
        
        # Create base navigation categories
        categories = [
            ('Tools', 'fa-tools', 'System tools and utilities'),
            ('Admin', 'fa-shield', 'Administrative functions'),
            ('Reports', 'fa-chart-bar', 'System reports'),
            ('Settings', 'fa-cog', 'System settings')
        ]
        
        for name, icon, description in categories:
            session.execute(
                sa.text(
                    'INSERT INTO navigation_category (name, icon, description, created_at, created_by) '
                    'VALUES (:name, :icon, :description, :created_at, :created_by)'
                ),
                {
                    'name': name,
                    'icon': icon,
                    'description': description,
                    'created_at': datetime.utcnow(),
                    'created_by': 'system'
                }
            )
        
        session.commit()
        
    except Exception as e:
        session.rollback()
        raise Exception(f"Error initializing RBAC data: {str(e)}")
    
    finally:
        session.close()

def downgrade():
    bind = op.get_bind()
    session = Session(bind=bind)
    
    try:
        # Delete base navigation categories
        session.execute(sa.text('DELETE FROM navigation_category'))
        
        # Delete base roles
        session.execute(sa.text('DELETE FROM role'))
        
        # Delete default actions
        session.execute(sa.text('DELETE FROM action'))
        
        session.commit()
        
    except Exception as e:
        session.rollback()
        raise Exception(f"Error removing RBAC data: {str(e)}")
    
    finally:
        session.close()
