from datetime import datetime
from app.extensions import db
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import event
from app.models.user import User  # Import the User model

class DatabaseConnection(db.Model):
    __tablename__ = 'database_connections'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    db_type = db.Column(db.String(20), nullable=False)  # oracle, mysql, sqlite
    host = db.Column(db.String(255))  # Not used for sqlite
    port = db.Column(db.Integer)      # Not used for sqlite
    database = db.Column(db.String(255), nullable=False)
    vault_path = db.Column(db.String(255), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships with explicit primaryjoin
    reports = db.relationship('Report', backref='connection', lazy=True, cascade='all, delete-orphan')
    created_by = db.relationship(
        'User',
        primaryjoin='DatabaseConnection.created_by_id == User.id',
        backref=db.backref('database_connections', lazy=True)
    )

class Report(db.Model):
    __tablename__ = 'database_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    connection_id = db.Column(db.Integer, db.ForeignKey('database_connections.id', ondelete='CASCADE'), nullable=False)
    query_config = db.Column(JSON, nullable=False)  # Stores table selections, joins, etc
    column_config = db.Column(JSON, nullable=False)  # Stores column customizations
    is_public = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    
    # Relationships with explicit primaryjoin
    created_by = db.relationship(
        'User',
        primaryjoin='Report.created_by_id == User.id',
        backref=db.backref('reports', lazy=True)
    )
    tags = db.relationship('ReportTagModel', secondary='report_tags_association', 
                         backref=db.backref('reports', lazy=True),
                         cascade='all, delete')
    history = db.relationship('ReportHistory', backref='report', lazy=True, 
                            cascade='all, delete-orphan')

class ReportTagModel(db.Model):
    __tablename__ = 'report_tags'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)

class ReportTag(db.Model):
    __tablename__ = 'report_tags_association'
    
    report_id = db.Column(db.Integer, db.ForeignKey('database_reports.id', ondelete='CASCADE'), primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey('report_tags.id', ondelete='CASCADE'), primary_key=True)

class ReportHistory(db.Model):
    __tablename__ = 'report_history'
    
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('database_reports.id', ondelete='CASCADE'), nullable=False)
    changed_by_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    changes = db.Column(JSON)  # Stores what changed in JSON format
    
    # Relationship with explicit primaryjoin
    changed_by = db.relationship(
        'User',
        primaryjoin='ReportHistory.changed_by_id == User.id',
        backref=db.backref('report_changes', lazy=True)
    )

# Event listener to track changes
@event.listens_for(Report, 'before_update')
def track_report_changes(mapper, connection, target):
    if target.id:  # Only track changes for existing reports
        history = ReportHistory(
            report_id=target.id,
            changed_by_id=target.created_by_id,  # Assuming current user is stored here
            changes={
                'title': target.title,
                'description': target.description,
                'query_config': target.query_config,
                'column_config': target.column_config,
                'is_public': target.is_public
            }
        )
        db.session.add(history)
