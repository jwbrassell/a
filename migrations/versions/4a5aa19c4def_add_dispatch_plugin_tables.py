"""Add dispatch plugin tables

Revision ID: 4a5aa19c4def
Revises: b1247bc8ba02
Create Date: 2024-12-05 08:40:33.915320

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4a5aa19c4def'
down_revision = 'b1247bc8ba02'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('dispatch_priorities',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=32), nullable=False),
    sa.Column('description', sa.String(length=256), nullable=True),
    sa.Column('color', sa.String(length=7), nullable=True),
    sa.Column('icon', sa.String(length=32), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('dispatch_teams',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=False),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('description', sa.String(length=256), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('dispatch_transactions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('team_id', sa.Integer(), nullable=False),
    sa.Column('priority_id', sa.Integer(), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('is_rma', sa.Boolean(), nullable=True),
    sa.Column('rma_info', sa.Text(), nullable=True),
    sa.Column('is_bridge', sa.Boolean(), nullable=True),
    sa.Column('bridge_link', sa.String(length=512), nullable=True),
    sa.Column('status', sa.String(length=32), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('created_by_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['created_by_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['priority_id'], ['dispatch_priorities.id'], ),
    sa.ForeignKeyConstraint(['team_id'], ['dispatch_teams.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('dispatch_transactions')
    op.drop_table('dispatch_teams')
    op.drop_table('dispatch_priorities')
    # ### end Alembic commands ###