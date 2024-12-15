"""Template plugin models."""

from app.extensions import db
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
import logging

# Configure logging
logger = logging.getLogger(__name__)

class TemplateModel(db.Model):
    """Example model for template plugin."""
    
    __tablename__ = 'template_items'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='active', index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    created_by = db.relationship('User', backref=db.backref('template_items', lazy='dynamic'))
    
    def __repr__(self):
        return f'<TemplateItem {self.name}>'
    
    @classmethod
    def create(cls, **kwargs):
        """Create a new template item."""
        try:
            item = cls(**kwargs)
            db.session.add(item)
            db.session.commit()
            logger.info(f"Created template item: {item.name}")
            return item
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error creating template item: {e}")
            raise
    
    def update(self, **kwargs):
        """Update template item."""
        try:
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            self.updated_at = datetime.utcnow()
            db.session.commit()
            logger.info(f"Updated template item: {self.name}")
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error updating template item: {e}")
            raise
    
    def delete(self):
        """Delete template item."""
        try:
            name = self.name
            db.session.delete(self)
            db.session.commit()
            logger.info(f"Deleted template item: {name}")
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error deleting template item: {e}")
            raise
    
    @classmethod
    def get_by_id(cls, item_id):
        """Get template item by ID."""
        try:
            return cls.query.get(item_id)
        except SQLAlchemyError as e:
            logger.error(f"Error getting template item by ID: {e}")
            raise
    
    @classmethod
    def get_by_name(cls, name):
        """Get template item by name."""
        try:
            return cls.query.filter_by(name=name).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting template item by name: {e}")
            raise
    
    @classmethod
    def get_active_items(cls):
        """Get all active template items."""
        try:
            return cls.query.filter_by(status='active').order_by(cls.created_at.desc()).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting active template items: {e}")
            raise
    
    def to_dict(self):
        """Convert template item to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'created_by': self.created_by.username
        }

def init_models():
    """Initialize plugin models."""
    try:
        # Create tables if they don't exist
        db.create_all()
        logger.info("Template plugin models initialized successfully")
    except SQLAlchemyError as e:
        logger.error(f"Error initializing template plugin models: {e}")
        raise
