"""Add document plugin tables

Revision ID: document_plugin_tables
Revises: handoff_tables
Create Date: 2024-01-09 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'document_plugin_tables'
down_revision = 'handoff_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Create document_categories table
    op.create_table(
        'document_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=64), nullable=False),
        sa.Column('description', sa.String(length=256), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create document_tags table
    op.create_table(
        'document_tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=256), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['category_id'], ['document_categories.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create document_changes table
    op.create_table(
        'document_changes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('changed_by', sa.Integer(), nullable=False),
        sa.Column('changed_at', sa.DateTime(), nullable=True),
        sa.Column('change_type', sa.String(length=32), nullable=False),
        sa.Column('previous_content', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['changed_by'], ['user.id'], ),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create document_tag_association table
    op.create_table(
        'document_tag_association',
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.ForeignKeyConstraint(['tag_id'], ['document_tags.id'], ),
        sa.PrimaryKeyConstraint('document_id', 'tag_id')
    )


def downgrade():
    op.drop_table('document_tag_association')
    op.drop_table('document_changes')
    op.drop_table('documents')
    op.drop_table('document_tags')
    op.drop_table('document_categories')
