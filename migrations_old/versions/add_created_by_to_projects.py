"""add created_by to projects

Revision ID: add_created_by_to_projects
Revises: ed19a22defcc
Create Date: 2024-01-10 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import String, MetaData, Table, select
from sqlalchemy.orm import Session

# revision identifiers, used by Alembic.
revision = 'add_created_by_to_projects'
down_revision = 'ed19a22defcc'
branch_labels = None
depends_on = None

def get_user_id_from_history(connection, project_id):
    """Get the first user_id from project history"""
    history_table = table('history',
        column('user_id', sa.Integer),
        column('project_id', sa.Integer),
        column('created_at', sa.DateTime)
    )
    
    result = connection.execute(
        select([history_table.c.user_id])
        .where(history_table.c.project_id == project_id)
        .order_by(history_table.c.created_at)
        .limit(1)
    ).first()
    
    return result.user_id if result else None

def get_username_from_user(connection, user_id):
    """Get username from user table"""
    if not user_id:
        return None
        
    user_table = table('user',
        column('id', sa.Integer),
        column('username', String)
    )
    
    result = connection.execute(
        select([user_table.c.username])
        .where(user_table.c.id == user_id)
    ).first()
    
    return result.username if result else None

def upgrade():
    # Create created_by column if it doesn't exist
    op.execute('SHOW COLUMNS FROM project LIKE "created_by"')
    result = op.get_bind().fetchone()
    if not result:
        op.add_column('project', sa.Column('created_by', sa.String(100)))
    
    # Create temporary table references
    project_table = table('project',
        column('id', sa.Integer),
        column('created_by', String),
        column('lead_id', sa.Integer)
    )
    
    connection = op.get_bind()
    
    # Get all projects without created_by
    projects = connection.execute(
        select([project_table.c.id, project_table.c.lead_id])
        .where(project_table.c.created_by.is_(None))
    ).fetchall()
    
    # Update each project
    for project_id, lead_id in projects:
        # Try to get creator from history first
        user_id = get_user_id_from_history(connection, project_id)
        
        # If no history, try to use lead_id
        if not user_id and lead_id:
            user_id = lead_id
            
        # Get username for the user_id
        username = get_username_from_user(connection, user_id)
        
        # Update the project
        connection.execute(
            project_table.update()
            .where(project_table.c.id == project_id)
            .values(created_by=username if username else 'system')
        )
    
    # Make created_by non-nullable after setting defaults
    op.alter_column('project', 'created_by',
        existing_type=sa.String(100),
        nullable=False
    )

def downgrade():
    # Make column nullable first
    op.alter_column('project', 'created_by',
        existing_type=sa.String(100),
        nullable=True
    )
    
    # Clear out created_by values
    project_table = table('project',
        column('created_by', String)
    )
    
    op.execute(
        project_table.update()
        .values(created_by=None)
    )
    
    # Drop the column
    op.drop_column('project', 'created_by')
