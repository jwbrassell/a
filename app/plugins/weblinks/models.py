"""Models for storing web links with metadata."""

from datetime import datetime
from typing import List, Optional
from app.extensions import db
from app.models import User

# Association table for many-to-many relationship between WebLinks and Tags
weblink_tag_association = db.Table('weblink_tag_association',
    db.Column('weblink_id', db.Integer, db.ForeignKey('weblinks.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('weblink_tags.id'), primary_key=True)
)

class WebLink(db.Model):
    """Model for storing web links with metadata."""
    __tablename__ = 'weblinks'
    
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), unique=True, nullable=False)
    friendly_name = db.Column(db.String(200), nullable=False)
    notes = db.Column(db.Text)
    icon = db.Column(db.String(100))  # Font Awesome icon class
    
    # User tracking
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)
    
    # Foreign keys
    category_id = db.Column(db.Integer, db.ForeignKey('weblink_categories.id'))
    
    # Relationships
    category = db.relationship('WebLinkCategory', backref=db.backref('links', lazy=True))
    tags = db.relationship('WebLinkTag', secondary=weblink_tag_association, backref=db.backref('links', lazy=True))
    creator = db.relationship('User', foreign_keys=[created_by], backref=db.backref('created_links', lazy=True))
    updater = db.relationship('User', foreign_keys=[updated_by], backref=db.backref('updated_links', lazy=True))

    def __repr__(self) -> str:
        return f'<WebLink {self.friendly_name}>'

    def to_dict(self) -> dict:
        """Convert web link to dictionary."""
        return {
            'id': self.id,
            'url': self.url,
            'friendly_name': self.friendly_name,
            'notes': self.notes,
            'icon': self.icon,
            'category': self.category.name if self.category else None,
            'tags': [tag.name for tag in self.tags],
            'created_by': self.creator.username,
            'updated_by': self.updater.username,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class WebLinkCategory(db.Model):
    """Model for web link categories."""
    __tablename__ = 'weblink_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    
    # User tracking
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[created_by], backref=db.backref('created_categories', lazy=True))
    updater = db.relationship('User', foreign_keys=[updated_by], backref=db.backref('updated_categories', lazy=True))

    def __repr__(self) -> str:
        return f'<WebLinkCategory {self.name}>'

    def to_dict(self) -> dict:
        """Convert category to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'created_by': self.creator.username,
            'updated_by': self.updater.username,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'link_count': len([link for link in self.links if link.deleted_at is None])
        }

class WebLinkTag(db.Model):
    """Model for web link tags."""
    __tablename__ = 'weblink_tags'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    
    # User tracking
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[created_by], backref=db.backref('created_tags', lazy=True))
    updater = db.relationship('User', foreign_keys=[updated_by], backref=db.backref('updated_tags', lazy=True))

    def __repr__(self) -> str:
        return f'<WebLinkTag {self.name}>'

    def to_dict(self) -> dict:
        """Convert tag to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'created_by': self.creator.username,
            'updated_by': self.updater.username,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'link_count': len([link for link in self.links if link.deleted_at is None])
        }
