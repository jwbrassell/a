"""add team to oncall rotation

Revision ID: add_team_to_oncall
Revises: add_oncall_plugin_tables
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'add_team_to_oncall'
down_revision = 'add_oncall_plugin_tables'
branch_labels = None
depends_on = None

def upgrade():
    # Create team table
    op.create_table(
        'oncall_team',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(50), nullable=False, unique=True),
        sa.Column('color', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), server_onupdate=sa.func.now())
    )
    
    # Create default team
    now = datetime.utcnow()
    op.execute(f"""
        INSERT INTO oncall_team (name, color, created_at, updated_at)
        VALUES ('Default Team', 'primary', '{now}', '{now}')
    """)
    
    # Create new rotation table with team_id
    op.create_table(
        'oncall_rotation_new',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('week_number', sa.Integer, nullable=False),
        sa.Column('year', sa.Integer, nullable=False),
        sa.Column('person_name', sa.String(100), nullable=False),
        sa.Column('phone_number', sa.String(20), nullable=False),
        sa.Column('team_id', sa.Integer, nullable=False),
        sa.Column('start_time', sa.DateTime, nullable=False),
        sa.Column('end_time', sa.DateTime, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), server_onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['team_id'], ['oncall_team.id'], name='fk_rotation_team')
    )
    
    # Copy data from old table to new table
    op.execute("""
        INSERT INTO oncall_rotation_new (
            id, week_number, year, person_name, phone_number, team_id,
            start_time, end_time, created_at, updated_at
        )
        SELECT 
            id, week_number, year, person_name, phone_number,
            (SELECT id FROM oncall_team WHERE name = 'Default Team'),
            start_time, end_time, created_at, updated_at
        FROM oncall_rotation
    """)
    
    # Drop old table
    op.drop_table('oncall_rotation')
    
    # Rename new table to original name
    op.rename_table('oncall_rotation_new', 'oncall_rotation')

def downgrade():
    # Create old rotation table without team_id
    op.create_table(
        'oncall_rotation_old',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('week_number', sa.Integer, nullable=False),
        sa.Column('year', sa.Integer, nullable=False),
        sa.Column('person_name', sa.String(100), nullable=False),
        sa.Column('phone_number', sa.String(20), nullable=False),
        sa.Column('start_time', sa.DateTime, nullable=False),
        sa.Column('end_time', sa.DateTime, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False)
    )
    
    # Copy data back excluding team_id
    op.execute("""
        INSERT INTO oncall_rotation_old (
            id, week_number, year, person_name, phone_number,
            start_time, end_time, created_at, updated_at
        )
        SELECT 
            id, week_number, year, person_name, phone_number,
            start_time, end_time, created_at, updated_at
        FROM oncall_rotation
    """)
    
    # Drop new tables
    op.drop_table('oncall_rotation')
    op.drop_table('oncall_team')
    
    # Rename old table to original name
    op.rename_table('oncall_rotation_old', 'oncall_rotation')
