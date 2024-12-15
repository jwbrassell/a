"""Models for the Reports plugin."""

from datetime import datetime
from app.extensions import db
from app.models import User, Role
from sqlalchemy.orm import relationship

# Association table for view permissions
view_role = db.Table('view_role',
    db.Column('view_id', db.Integer, db.ForeignKey('report_view.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True)
)

class DatabaseConnection(db.Model):
    """Model for storing database connection configurations."""
    
    __tablename__ = 'database_connection'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.String(256))
    db_type = db.Column(db.String(50), nullable=False)  # mysql, mariadb, sqlite
    host = db.Column(db.String(256))
    port = db.Column(db.Integer)
    database = db.Column(db.String(128))
    username = db.Column(db.String(128))
    # password field removed - now stored in vault
    
    # User tracking
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    views = relationship('ReportView', backref='database', lazy=True)
    creator = relationship('User', foreign_keys=[created_by], backref='database_connections_created')
    updater = relationship('User', foreign_keys=[updated_by], backref='database_connections_updated')

    def __repr__(self):
        return f'<DatabaseConnection {self.name}>'

    def to_dict(self):
        """Convert database connection to dictionary for API responses."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'db_type': self.db_type,
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'username': self.username,
            'is_active': self.is_active,
            'created_by': self.created_by,
            'updated_by': self.updated_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None
        }

class ReportView(db.Model):
    """Model for storing report view configurations."""
    
    __tablename__ = 'report_view'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    database_id = db.Column(db.Integer, db.ForeignKey('database_connection.id'), nullable=False)
    query = db.Column(db.Text, nullable=False)  # SQL query
    column_config = db.Column(db.JSON, nullable=False)  # Column headers, sorting, filtering config
    is_private = db.Column(db.Boolean, default=False)
    
    # User tracking
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)
    last_run = db.Column(db.DateTime)
    
    # Relationships
    creator = relationship('User', foreign_keys=[created_by], backref='report_views_created')
    updater = relationship('User', foreign_keys=[updated_by], backref='report_views_updated')
    roles = relationship('Role', secondary=view_role, backref=db.backref('report_views', lazy=True))

    def __repr__(self):
        return f'<ReportView {self.title}>'

    def to_dict(self):
        """Convert view to dictionary for API responses."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'database_id': self.database_id,
            'query': self.query,
            'column_config': self.column_config,
            'is_private': self.is_private,
            'created_by': self.created_by,
            'updated_by': self.updated_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
            'last_run': self.last_run.isoformat() if self.last_run else None
        }
