from datetime import datetime
from app.extensions import db
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
    title = db.Column(db.String(256), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)  # HTML content from TinyMCE
    category_id = db.Column(db.Integer, db.ForeignKey('document_categories.id'), nullable=False, index=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)
    is_template = db.Column(db.Boolean, default=False)
    template_name = db.Column(db.String(256))
    is_private = db.Column(db.Boolean, default=False)

    # Relationships
    category = db.relationship('DocumentCategory', backref='documents')
    creator = db.relationship('User', backref='documents', foreign_keys=[created_by])
    tags = db.relationship('DocumentTag', secondary=document_tag_association, backref='documents')
    changes = db.relationship('DocumentChange', backref='document', lazy='dynamic')
    shared_with = db.relationship('DocumentShare', back_populates='document', cascade='all, delete-orphan')
    cached_versions = db.relationship('DocumentCache', back_populates='document', cascade='all, delete-orphan')

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
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M'),
            'is_template': self.is_template,
            'template_name': self.template_name,
            'is_private': self.is_private
        }

    def user_can_access(self, user):
        """Check if a user can access this document."""
        if not self.is_private:
            return True
        if user.id == self.created_by:
            return True
        return any(share.user_id == user.id for share in self.shared_with)

    def user_can_edit(self, user):
        """Check if a user can edit this document."""
        if user.id == self.created_by:
            return True
        return any(share.user_id == user.id and share.permission in ['write', 'admin'] 
                  for share in self.shared_with)

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

class DocumentShare(db.Model):
    """Model for document sharing permissions."""
    __tablename__ = 'document_shares'
    
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    permission = db.Column(db.String(32), nullable=False)  # read, write, admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relationships
    document = db.relationship('Document', back_populates='shared_with')
    user = db.relationship('User', foreign_keys=[user_id], backref='shared_documents')
    creator = db.relationship('User', foreign_keys=[created_by])

    def __repr__(self):
        return f'<DocumentShare {self.document_id} - {self.user.username}>'

class DocumentCache(db.Model):
    """Model for caching frequently accessed documents."""
    __tablename__ = 'document_caches'
    
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)  # Cached content
    format = db.Column(db.String(32), nullable=False)  # html, pdf, doc
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    access_count = db.Column(db.Integer, default=0)

    # Relationships
    document = db.relationship('Document', back_populates='cached_versions')

    def __repr__(self):
        return f'<DocumentCache {self.document_id} - {self.format}>'

    @property
    def is_expired(self):
        """Check if the cache has expired."""
        return datetime.utcnow() > self.expires_at
