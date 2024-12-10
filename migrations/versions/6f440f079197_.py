"""empty message

Revision ID: 6f440f079197
Revises: document_plugin_tables
Create Date: 2024-12-05 20:30:44.273066

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision = '6f440f079197'
down_revision = 'document_plugin_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Check if table already exists before trying to create it
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()
    
    if 'document_tag_association' not in tables:
        op.create_table('document_tag_association',
            sa.Column('document_id', sa.Integer(), nullable=False),
            sa.Column('tag_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
            sa.ForeignKeyConstraint(['tag_id'], ['document_tags.id'], ),
            sa.PrimaryKeyConstraint('document_id', 'tag_id')
        )


def downgrade():
    # Only drop if exists
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()
    
    if 'document_tag_association' in tables:
        op.drop_table('document_tag_association')
