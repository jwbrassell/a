from app.extensions import db
from datetime import datetime
from sqlalchemy import JSON

class AWSConfiguration(db.Model):
    """Model for AWS configurations"""
    __tablename__ = 'aws_configurations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    regions = db.Column(JSON, nullable=False)
    vault_path = db.Column(db.String(255), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<AWSConfiguration {self.name}>'
    
    def to_dict(self):
        """Convert configuration to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'regions': self.regions,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
