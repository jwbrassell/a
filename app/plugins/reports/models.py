from datetime import datetime
from app.extensions import db
from app.models import User, Role

# Association table for view permissions
view_role = db.Table('view_role',
    db.Column('view_id', db.Integer, db.ForeignKey('report_view.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True)
)

class DatabaseConnection(db.Model):
    """Model for storing database connection configurations."""
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.String(256))
    db_type = db.Column(db.String(50), nullable=False)  # mysql, mariadb, sqlite
    host = db.Column(db.String(256))
    port = db.Column(db.Integer)
    database = db.Column(db.String(128))
    username = db.Column(db.String(128))
    # password field removed - now stored in vault
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    views = db.relationship('ReportView', backref='database', lazy=True)
    creator = db.relationship('User', backref='database_connections')

    def __repr__(self):
        return f'<DatabaseConnection {self.name}>'

class ReportView(db.Model):
    """Model for storing report view configurations."""
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    database_id = db.Column(db.Integer, db.ForeignKey('database_connection.id'), nullable=False)
    query = db.Column(db.Text, nullable=False)  # SQL query
    column_config = db.Column(db.JSON, nullable=False)  # Column headers, sorting, filtering config
    is_private = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_run = db.Column(db.DateTime)
    
    # Relationships
    creator = db.relationship('User', backref='report_views')
    roles = db.relationship('Role', secondary=view_role, backref=db.backref('report_views', lazy=True))

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
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_run': self.last_run.isoformat() if self.last_run else None
        }
