from datetime import datetime
from app.extensions import db
from app.models.user import User
from sqlalchemy import event, JSON

class WebLink(db.Model):
    __tablename__ = 'weblinks'
    
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False, unique=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(100))  # Font Awesome icon class
    created_by = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    click_count = db.Column(db.Integer, default=0)
    
    # Relationships
    tags = db.relationship('Tag', secondary='weblink_tags', backref='weblinks')
    history = db.relationship('WebLinkHistory', backref='weblink', lazy='dynamic',
                            cascade='all, delete-orphan')
    creator = db.relationship(
        'User',
        primaryjoin='WebLink.created_by == User.id',
        backref=db.backref('weblinks', lazy='dynamic'),
        remote_side='User.id'
    )

class Tag(db.Model):
    __tablename__ = 'tags'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Association table for many-to-many relationship between WebLinks and Tags
weblink_tags = db.Table('weblink_tags',
    db.Column('weblink_id', db.Integer, db.ForeignKey('weblinks.id', ondelete='CASCADE'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
)

class WebLinkHistory(db.Model):
    __tablename__ = 'weblink_history'
    
    id = db.Column(db.Integer, primary_key=True)
    weblink_id = db.Column(db.Integer, db.ForeignKey('weblinks.id', ondelete='CASCADE'))
    changed_by = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    changes = db.Column(JSON)  # Store changes as JSON
    
    editor = db.relationship(
        'User',
        primaryjoin='WebLinkHistory.changed_by == User.id',
        backref=db.backref('weblink_edits', lazy='dynamic'),
        remote_side='User.id'
    )

# Event listeners to ensure JSON compatibility with SQLite
@event.listens_for(WebLinkHistory, 'before_insert')
def convert_json_before_insert(mapper, connection, target):
    if isinstance(target.changes, dict):
        import json
        target.changes = json.dumps(target.changes)

@event.listens_for(WebLinkHistory, 'load')
def convert_json_on_load(target, context):
    if isinstance(target.changes, str):
        import json
        target.changes = json.loads(target.changes)
