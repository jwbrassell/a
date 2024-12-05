"""Add dispatch plugin route mappings

Revision ID: dispatch_route_mappings
Revises: 4a5aa19c4def
Create Date: 2024-12-05 09:40:33.915320

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'dispatch_route_mappings'
down_revision = '4a5aa19c4def'
branch_labels = None
depends_on = None

def upgrade():
    # Get the connection
    conn = op.get_bind()
    
    # Insert route mappings for dispatch plugin
    conn.execute("""
        INSERT INTO page_route_mapping (page_name, route, icon, weight, created_at, updated_at)
        VALUES 
        ('Dispatch Tool', '/dispatch/', 'fa-paper-plane', 10, :timestamp, :timestamp),
        ('Submit Dispatch', '/dispatch/submit', 'fa-plus', 11, :timestamp, :timestamp),
        ('Dispatch Transactions', '/dispatch/transactions', 'fa-list', 12, :timestamp, :timestamp),
        ('Manage Dispatch', '/dispatch/manage', 'fa-cog', 13, :timestamp, :timestamp),
        ('Add Team', '/dispatch/team', 'fa-users', 14, :timestamp, :timestamp),
        ('Add Priority', '/dispatch/priority', 'fa-flag', 15, :timestamp, :timestamp)
    """, {'timestamp': datetime.utcnow()})

def downgrade():
    # Remove dispatch route mappings
    conn = op.get_bind()
    conn.execute("""
        DELETE FROM page_route_mapping 
        WHERE route LIKE '/dispatch/%'
    """)
