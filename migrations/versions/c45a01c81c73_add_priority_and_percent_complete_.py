"""Add priority and percent_complete fields to Project model

Revision ID: c45a01c81c73
Revises: 495d7e833294
Create Date: 2024-12-06 11:06:40.885983

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c45a01c81c73'
down_revision = '495d7e833294'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('project', schema=None) as batch_op:
        batch_op.add_column(sa.Column('priority', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('percent_complete', sa.Integer(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('project', schema=None) as batch_op:
        batch_op.drop_column('percent_complete')
        batch_op.drop_column('priority')

    # ### end Alembic commands ###
