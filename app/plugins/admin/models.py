"""
Models for the admin monitoring system
"""
from datetime import datetime
from app.extensions import db

class SystemMetric(db.Model):
    """System-level metrics like CPU, memory, disk usage"""
    __tablename__ = 'system_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    metric_type = db.Column(db.String(50), index=True)  # cpu, memory, disk, etc.
    value = db.Column(db.Float)
    unit = db.Column(db.String(20))  # %, MB, GB, etc.
    
    def __repr__(self):
        return f'<SystemMetric {self.metric_type}: {self.value}{self.unit}>'
        
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'metric_type': self.metric_type,
            'value': self.value,
            'unit': self.unit
        }

class ApplicationMetric(db.Model):
    """Application-level metrics like response times, error rates"""
    __tablename__ = 'application_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    metric_type = db.Column(db.String(50), index=True)  # response_time, error_rate, etc.
    endpoint = db.Column(db.String(200), index=True, nullable=True)
    value = db.Column(db.Float)
    unit = db.Column(db.String(20))  # ms, %, etc.
    
    def __repr__(self):
        return f'<ApplicationMetric {self.metric_type}: {self.value}{self.unit}>'
        
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'metric_type': self.metric_type,
            'endpoint': self.endpoint,
            'value': self.value,
            'unit': self.unit
        }

class UserMetric(db.Model):
    """User activity and engagement metrics"""
    __tablename__ = 'user_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    metric_type = db.Column(db.String(50), index=True)  # active_users, session_duration, etc.
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    value = db.Column(db.Float)
    unit = db.Column(db.String(20))  # minutes, count, etc.
    
    def __repr__(self):
        return f'<UserMetric {self.metric_type}: {self.value}{self.unit}>'
        
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'metric_type': self.metric_type,
            'user_id': self.user_id,
            'value': self.value,
            'unit': self.unit
        }

class FeatureUsage(db.Model):
    """Feature-level usage tracking"""
    __tablename__ = 'feature_usage'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    feature = db.Column(db.String(100), index=True)
    plugin = db.Column(db.String(50), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    duration = db.Column(db.Integer, nullable=True)  # in seconds
    success = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<FeatureUsage {self.plugin}.{self.feature}>'
        
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'feature': self.feature,
            'plugin': self.plugin,
            'user_id': self.user_id,
            'duration': self.duration,
            'success': self.success
        }

class ResourceMetric(db.Model):
    """Resource utilization metrics (time, cost, etc.)"""
    __tablename__ = 'resource_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    resource_type = db.Column(db.String(50), index=True)  # time, cost, storage, etc.
    category = db.Column(db.String(50), index=True)
    value = db.Column(db.Float)
    unit = db.Column(db.String(20))  # hours, USD, GB, etc.
    
    def __repr__(self):
        return f'<ResourceMetric {self.resource_type}: {self.value}{self.unit}>'
        
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'resource_type': self.resource_type,
            'category': self.category,
            'value': self.value,
            'unit': self.unit
        }
