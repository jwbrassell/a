from datetime import datetime
from app import db
from flask_login import current_user

# Association table for document tags
document_tag_association = db.Table('document_tag_association',
    db.Column('document_id', db.Integer, db.ForeignKey('documents.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('document_tags.id'), primary_key=True)
)

class Document(db.Model):
    """Model for storing rich text documents."""
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), nullable=False)
    content = db.Column(db.Text, nullable=False)  # HTML content from TinyMCE
    category_id = db.Column(db.Integer, db.ForeignKey('document_categories.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    category = db.relationship('DocumentCategory', backref='documents')
    creator = db.relationship('User', backref='documents', foreign_keys=[created_by])
    tags = db.relationship('DocumentTag', secondary=document_tag_association, backref='documents')
    changes = db.relationship('DocumentChange', backref='document', lazy='dynamic')

    def __repr__(self):
        return f'<Document {self.title}>'

    def to_dict(self):
        """Convert document to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'category': self.category.name,
            'tags': [tag.name for tag in self.tags],
            'created_by': self.creator.username,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M')
        }

class DocumentCategory(db.Model):
    """Model for document categories."""
    __tablename__ = 'document_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False, unique=True)
    description = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<DocumentCategory {self.name}>'

class DocumentTag(db.Model):
    """Model for document tags."""
    __tablename__ = 'document_tags'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<DocumentTag {self.name}>'

class DocumentChange(db.Model):
    """Model for tracking document changes."""
    __tablename__ = 'document_changes'
    
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    changed_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    change_type = db.Column(db.String(32), nullable=False)  # create, update, delete
    previous_content = db.Column(db.Text)  # Store previous content for history

    # Relationships
    editor = db.relationship('User', backref='document_changes')

    def __repr__(self):
        return f'<DocumentChange {self.document_id} by {self.editor.username}>'
