"""Add parent_id field to Task model for sub-tasks

Revision ID: task_updates_migration
Revises: ed19a22defcc
Create Date: 2024-01-10 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'task_updates_migration'
down_revision = 'ed19a22defcc'
branch_labels = None
depends_on = None


def upgrade():
    # Add parent_id and its foreign key
    with op.batch_alter_table('task', schema=None) as batch_op:
        batch_op.add_column(sa.Column('parent_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_task_parent_id',
            'task', ['parent_id'], ['id'],
            ondelete='CASCADE'
        )


def downgrade():
    # Remove the foreign key and parent_id
    with op.batch_alter_table('task', schema=None) as batch_op:
        batch_op.drop_constraint('fk_task_parent_id', type_='foreignkey')
        batch_op.drop_column('parent_id')
