from app.extensions import db
from datetime import datetime
from sqlalchemy import JSON

class EC2Instance(db.Model):
    """Model for EC2 instances"""
    __tablename__ = 'aws_ec2_instances'

    id = db.Column(db.Integer, primary_key=True)
    aws_config_id = db.Column(db.Integer, db.ForeignKey('aws_configurations.id'), nullable=False)
    instance_id = db.Column(db.String(100), unique=True, nullable=False)
    region = db.Column(db.String(50), nullable=False)
    instance_type = db.Column(db.String(50), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    public_ip = db.Column(db.String(45))
    private_ip = db.Column(db.String(45))
    launch_time = db.Column(db.DateTime(timezone=True), nullable=False)
    tags = db.Column(JSON, default={})
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    configuration = db.relationship('AWSConfiguration', backref=db.backref('ec2_instances', lazy=True))
    
    def __repr__(self):
        return f'<EC2Instance {self.instance_id}>'
    
    def to_dict(self):
        """Convert instance to dictionary"""
        return {
            'id': self.id,
            'instance_id': self.instance_id,
            'region': self.region,
            'instance_type': self.instance_type,
            'state': self.state,
            'public_ip': self.public_ip,
            'private_ip': self.private_ip,
            'launch_time': self.launch_time.isoformat(),
            'tags': self.tags,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
