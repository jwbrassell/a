"""empty message

Revision ID: 8803065dd675
Revises: 0bb7ce556a77, rename_todo_order_column
Create Date: 2024-12-09 02:20:32.942312

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8803065dd675'
down_revision = ('0bb7ce556a77', 'rename_todo_order_column')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
