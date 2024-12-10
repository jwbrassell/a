"""merge heads

Revision ID: merge_heads
Revises: add_created_by_to_projects, add_team_to_oncall
Create Date: 2024-12-10 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'merge_heads'
down_revision = None
branch_labels = None
depends_on = ('add_created_by_to_projects', 'add_team_to_oncall')

def upgrade():
    pass

def downgrade():
    pass
