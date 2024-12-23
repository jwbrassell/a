from app.extensions import db
from datetime import datetime
from sqlalchemy import JSON

class AWSHealthEvent(db.Model):
    """Model for AWS Health events"""
    __tablename__ = 'aws_health_events'

    id = db.Column(db.Integer, primary_key=True)
    aws_config_id = db.Column(db.Integer, db.ForeignKey('aws_configurations.id'), nullable=False)
    event_arn = db.Column(db.String(255), unique=True, nullable=False)
    service = db.Column(db.String(100), nullable=False)
    event_type_code = db.Column(db.String(100), nullable=False)
    event_type_category = db.Column(db.String(100), nullable=False)
    region = db.Column(db.String(50))
    start_time = db.Column(db.DateTime(timezone=True), nullable=False)
    end_time = db.Column(db.DateTime(timezone=True))
    status = db.Column(db.String(50), nullable=False)
    affected_resources = db.Column(JSON, default=list)
    description = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    configuration = db.relationship('AWSConfiguration', backref=db.backref('health_events', lazy=True))
    
    def __repr__(self):
        return f'<AWSHealthEvent {self.event_arn}>'
    
    def to_dict(self):
        """Convert event to dictionary"""
        return {
            'id': self.id,
            'event_arn': self.event_arn,
            'service': self.service,
            'event_type_code': self.event_type_code,
            'event_type_category': self.event_type_category,
            'region': self.region,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status,
            'affected_resources': self.affected_resources,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
