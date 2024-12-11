from datetime import datetime
from app import db

# Association table for many-to-many relationship between WebLinks and Tags
weblink_tag_association = db.Table('weblink_tag_association',
    db.Column('weblink_id', db.Integer, db.ForeignKey('weblinks.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('weblink_tags.id'), primary_key=True)
)

class WebLink(db.Model):
    """Model for storing web links with metadata"""
    __tablename__ = 'weblinks'
    
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), unique=True, nullable=False)
    friendly_name = db.Column(db.String(200), nullable=False)
    notes = db.Column(db.Text)
    icon = db.Column(db.String(100))  # Font Awesome icon class
    created_by = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    category_id = db.Column(db.Integer, db.ForeignKey('weblink_categories.id'))
    
    # Relationships
    category = db.relationship('WebLinkCategory', backref='links')
    tags = db.relationship('WebLinkTag', secondary=weblink_tag_association, backref='links')

    def __repr__(self):
        return f'<WebLink {self.friendly_name}>'

    def to_dict(self):
        """Convert web link to dictionary"""
        return {
            'id': self.id,
            'url': self.url,
            'friendly_name': self.friendly_name,
            'notes': self.notes,
            'icon': self.icon,
            'category': self.category.name if self.category else None,
            'tags': [tag.name for tag in self.tags],
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class WebLinkCategory(db.Model):
    """Model for web link categories"""
    __tablename__ = 'weblink_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    created_by = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<WebLinkCategory {self.name}>'

    def to_dict(self):
        """Convert category to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'link_count': len(self.links)
        }

class WebLinkTag(db.Model):
    """Model for web link tags"""
    __tablename__ = 'weblink_tags'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    created_by = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<WebLinkTag {self.name}>'

    def to_dict(self):
        """Convert tag to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'link_count': len(self.links)
        }
