"""Models for storing application metrics."""

from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy import Index, func
from typing import Dict, Any, List
import json

class Metric(db.Model):
    """Model for storing metric data points."""
    
    __tablename__ = 'metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False, index=True)
    value = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    tags = db.Column(JSON, nullable=False, default=dict)
    metric_type = db.Column(db.String(20), nullable=False, index=True)  # gauge, counter, histogram
    
    # Create composite index for efficient querying
    __table_args__ = (
        Index('idx_metrics_name_timestamp', 'name', 'timestamp'),
    )
    
    def __repr__(self):
        return f'<Metric {self.name}:{self.value} @ {self.timestamp}>'
    
    @classmethod
    def get_metrics_by_name(cls, name: str, start_time: datetime = None,
                           end_time: datetime = None, tags: Dict[str, str] = None) -> List['Metric']:
        """Get metrics by name with optional time range and tags."""
        query = cls.query.filter_by(name=name)
        
        if start_time:
            query = query.filter(cls.timestamp >= start_time)
        if end_time:
            query = query.filter(cls.timestamp <= end_time)
        if tags:
            # Match all provided tags
            for key, value in tags.items():
                query = query.filter(cls.tags[key].astext == value)
        
        return query.order_by(cls.timestamp.desc()).all()
    
    @classmethod
    def get_metric_statistics(cls, name: str, start_time: datetime = None,
                            end_time: datetime = None, tags: Dict[str, str] = None) -> Dict[str, Any]:
        """Get statistical information about a metric."""
        query = cls.query.filter_by(name=name)
        
        if start_time:
            query = query.filter(cls.timestamp >= start_time)
        if end_time:
            query = query.filter(cls.timestamp <= end_time)
        if tags:
            for key, value in tags.items():
                query = query.filter(cls.tags[key].astext == value)
        
        stats = query.with_entities(
            func.min(cls.value).label('min'),
            func.max(cls.value).label('max'),
            func.avg(cls.value).label('avg'),
            func.count(cls.value).label('count')
        ).first()
        
        return {
            'min': stats.min,
            'max': stats.max,
            'avg': stats.avg,
            'count': stats.count,
            'name': name,
            'start_time': start_time,
            'end_time': end_time,
            'tags': tags
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metric to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'value': self.value,
            'timestamp': self.timestamp.isoformat(),
            'tags': json.loads(self.tags) if isinstance(self.tags, str) else self.tags,
            'metric_type': self.metric_type
        }

class MetricAlert(db.Model):
    """Model for metric-based alerts."""
    
    __tablename__ = 'metric_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    metric_name = db.Column(db.String(128), nullable=False)
    condition = db.Column(db.String(64), nullable=False)  # >, <, =, !=, >=, <=
    threshold = db.Column(db.Float, nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # Duration in seconds
    tags = db.Column(JSON, nullable=False, default=dict)
    enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_triggered = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<MetricAlert {self.name}:{self.metric_name} {self.condition} {self.threshold}>'
    
    def check_condition(self, value: float) -> bool:
        """Check if value meets alert condition."""
        if self.condition == '>':
            return value > self.threshold
        elif self.condition == '<':
            return value < self.threshold
        elif self.condition == '=':
            return value == self.threshold
        elif self.condition == '!=':
            return value != self.threshold
        elif self.condition == '>=':
            return value >= self.threshold
        elif self.condition == '<=':
            return value <= self.threshold
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'metric_name': self.metric_name,
            'condition': self.condition,
            'threshold': self.threshold,
            'duration': self.duration,
            'tags': json.loads(self.tags) if isinstance(self.tags, str) else self.tags,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat(),
            'last_triggered': self.last_triggered.isoformat() if self.last_triggered else None
        }

class MetricDashboard(db.Model):
    """Model for custom metric dashboards."""
    
    __tablename__ = 'metric_dashboards'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    layout = db.Column(JSON, nullable=False)  # Dashboard widget layout
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    created_by = db.relationship('User', backref=db.backref('dashboards', lazy='dynamic'))
    
    def __repr__(self):
        return f'<MetricDashboard {self.name}>'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert dashboard to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'layout': json.loads(self.layout) if isinstance(self.layout, str) else self.layout,
            'created_by': self.created_by.username,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

def init_metrics_models():
    """Initialize metrics models."""
    db.create_all()
