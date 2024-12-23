from app.extensions import db
from datetime import datetime
from sqlalchemy import JSON

class EC2Template(db.Model):
    """Model for EC2 launch templates"""
    __tablename__ = 'aws_ec2_templates'

    id = db.Column(db.Integer, primary_key=True)
    aws_config_id = db.Column(db.Integer, db.ForeignKey('aws_configurations.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    instance_type = db.Column(db.String(50), nullable=False)
    ami_id = db.Column(db.String(100), nullable=False)
    key_name = db.Column(db.String(100))
    security_groups = db.Column(JSON, default=[])  # Store as JSON array
    user_data = db.Column(db.Text)
    tags = db.Column(JSON, default={})
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    configuration = db.relationship('AWSConfiguration', backref=db.backref('ec2_templates', lazy=True))
    
    def __repr__(self):
        return f'<EC2Template {self.name}>'
    
    def to_dict(self):
        """Convert template to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'instance_type': self.instance_type,
            'ami_id': self.ami_id,
            'key_name': self.key_name,
            'security_groups': self.security_groups,
            'user_data': self.user_data,
            'tags': self.tags,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def get_launch_config(self) -> dict:
        """Get configuration for launching instances"""
        return {
            'ami_id': self.ami_id,
            'instance_type': self.instance_type,
            'key_name': self.key_name,
            'security_groups': self.security_groups,
            'user_data': self.user_data,
            'tags': self.tags
        }
