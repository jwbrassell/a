"""Analytics models for business intelligence features."""

from app.extensions import db
from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy import func, and_, case, JSON
from collections import defaultdict

class FeatureUsage(db.Model):
    """Track feature usage statistics."""
    
    __tablename__ = 'feature_usage'
    
    id = db.Column(db.Integer, primary_key=True)
    feature_name = db.Column(db.String(128), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    duration = db.Column(db.Float)  # Duration in seconds
    action = db.Column(db.String(64))  # e.g., 'view', 'edit', 'delete'
    success = db.Column(db.Boolean, default=True)
    context_data = db.Column(JSON)  # Store as JSON
    
    # Relationships
    user = db.relationship('User', backref=db.backref('feature_usage', lazy='dynamic'))
    
    @staticmethod
    def record_usage(feature_name: str, user_id: int, action: str = None,
                    duration: float = None, success: bool = True,
                    metadata: Dict = None) -> 'FeatureUsage':
        """Record a feature usage event."""
        import json
        usage = FeatureUsage(
            feature_name=feature_name,
            user_id=user_id,
            action=action,
            duration=duration,
            success=success,
            context_data=json.dumps(metadata) if metadata else None
        )
        db.session.add(usage)
        db.session.commit()
        return usage
    
    @staticmethod
    def get_popular_features(days: int = 30, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most popular features in the last N days."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        return db.session.query(
            FeatureUsage.feature_name,
            func.count(FeatureUsage.id).label('usage_count'),
            func.avg(FeatureUsage.duration).label('avg_duration'),
            func.sum(case((FeatureUsage.success.is_(True), 1), else_=0)).label('success_count')
        ).filter(
            FeatureUsage.timestamp >= cutoff
        ).group_by(
            FeatureUsage.feature_name
        ).order_by(
            func.count(FeatureUsage.id).desc()
        ).limit(limit).all()

class DocumentAnalytics(db.Model):
    """Track document access and usage patterns."""
    
    __tablename__ = 'document_analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, nullable=False, index=True)
    category = db.Column(db.String(64), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    action = db.Column(db.String(64))  # e.g., 'view', 'download', 'edit'
    duration = db.Column(db.Float)  # Time spent viewing/editing
    context_data = db.Column(JSON)  # Store as JSON
    
    # Relationships
    user = db.relationship('User', backref=db.backref('document_access', lazy='dynamic'))
    
    @staticmethod
    def record_access(document_id: int, category: str, user_id: int,
                     action: str, duration: float = None,
                     metadata: Dict = None) -> 'DocumentAnalytics':
        """Record a document access event."""
        import json
        access = DocumentAnalytics(
            document_id=document_id,
            category=category,
            user_id=user_id,
            action=action,
            duration=duration,
            context_data=json.dumps(metadata) if metadata else None
        )
        db.session.add(access)
        db.session.commit()
        return access
    
    @staticmethod
    def get_popular_categories(days: int = 30, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most accessed document categories."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        return db.session.query(
            DocumentAnalytics.category,
            func.count(DocumentAnalytics.id).label('access_count'),
            func.count(func.distinct(DocumentAnalytics.user_id)).label('unique_users'),
            func.avg(DocumentAnalytics.duration).label('avg_duration')
        ).filter(
            DocumentAnalytics.timestamp >= cutoff
        ).group_by(
            DocumentAnalytics.category
        ).order_by(
            func.count(DocumentAnalytics.id).desc()
        ).limit(limit).all()

class ProjectMetrics(db.Model):
    """Track project performance and completion metrics."""
    
    __tablename__ = 'project_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, nullable=False, index=True)
    metric_name = db.Column(db.String(64), nullable=False)  # e.g., 'completion_rate', 'time_spent'
    value = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    context_data = db.Column(JSON)  # Store as JSON
    
    @staticmethod
    def record_metric(project_id: int, metric_name: str, value: float,
                     metadata: Dict = None) -> 'ProjectMetrics':
        """Record a project metric."""
        import json
        metric = ProjectMetrics(
            project_id=project_id,
            metric_name=metric_name,
            value=value,
            context_data=json.dumps(metadata) if metadata else None
        )
        db.session.add(metric)
        db.session.commit()
        return metric
    
    @staticmethod
    def get_project_performance(project_id: int) -> Dict[str, Any]:
        """Get comprehensive project performance metrics."""
        metrics = ProjectMetrics.query.filter_by(project_id=project_id).all()
        performance = defaultdict(list)
        for metric in metrics:
            import json
            context_data = json.loads(metric.context_data) if metric.context_data else None
            performance[metric.metric_name].append({
                'value': metric.value,
                'timestamp': metric.timestamp,
                'context_data': context_data
            })
        return dict(performance)

class TeamProductivity(db.Model):
    """Track team productivity metrics."""
    
    __tablename__ = 'team_productivity'
    
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    metric_name = db.Column(db.String(64), nullable=False)  # e.g., 'tasks_completed', 'hours_logged'
    value = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    context_data = db.Column(JSON)  # Store as JSON
    
    # Relationships
    user = db.relationship('User', backref=db.backref('productivity_metrics', lazy='dynamic'))
    
    @staticmethod
    def record_productivity(team_id: int, user_id: int, metric_name: str,
                          value: float, metadata: Dict = None) -> 'TeamProductivity':
        """Record a team productivity metric."""
        import json
        metric = TeamProductivity(
            team_id=team_id,
            user_id=user_id,
            metric_name=metric_name,
            value=value,
            context_data=json.dumps(metadata) if metadata else None
        )
        db.session.add(metric)
        db.session.commit()
        return metric
    
    @staticmethod
    def get_team_performance(team_id: int, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive team performance metrics."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        metrics = db.session.query(
            TeamProductivity.metric_name,
            func.avg(TeamProductivity.value).label('avg_value'),
            func.min(TeamProductivity.value).label('min_value'),
            func.max(TeamProductivity.value).label('max_value'),
            func.count(func.distinct(TeamProductivity.user_id)).label('active_users')
        ).filter(
            and_(
                TeamProductivity.team_id == team_id,
                TeamProductivity.timestamp >= cutoff
            )
        ).group_by(
            TeamProductivity.metric_name
        ).all()
        
        return {
            metric.metric_name: {
                'avg_value': metric.avg_value,
                'min_value': metric.min_value,
                'max_value': metric.max_value,
                'active_users': metric.active_users
            }
            for metric in metrics
        }

class ResourceUtilization(db.Model):
    """Track resource utilization and allocation."""
    
    __tablename__ = 'resource_utilization'
    
    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.Integer, nullable=False, index=True)
    resource_type = db.Column(db.String(64), nullable=False, index=True)  # e.g., 'server', 'license', 'equipment'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    project_id = db.Column(db.Integer, index=True)
    utilization = db.Column(db.Float, nullable=False)  # Percentage or count
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    cost = db.Column(db.Float)  # Cost associated with usage
    context_data = db.Column(JSON)  # Store as JSON
    
    # Relationships
    user = db.relationship('User', backref=db.backref('resource_usage', lazy='dynamic'))
    
    @staticmethod
    def record_utilization(resource_id: int, resource_type: str,
                          utilization: float, start_time: datetime,
                          user_id: int = None, project_id: int = None,
                          end_time: datetime = None, cost: float = None,
                          metadata: Dict = None) -> 'ResourceUtilization':
        """Record resource utilization."""
        import json
        usage = ResourceUtilization(
            resource_id=resource_id,
            resource_type=resource_type,
            user_id=user_id,
            project_id=project_id,
            utilization=utilization,
            start_time=start_time,
            end_time=end_time,
            cost=cost,
            context_data=json.dumps(metadata) if metadata else None
        )
        db.session.add(usage)
        db.session.commit()
        return usage
    
    @staticmethod
    def get_resource_metrics(resource_type: str = None,
                           days: int = 30) -> Dict[str, Any]:
        """Get resource utilization metrics."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        query = db.session.query(
            ResourceUtilization.resource_type,
            func.avg(ResourceUtilization.utilization).label('avg_utilization'),
            func.sum(ResourceUtilization.cost).label('total_cost'),
            func.count(func.distinct(ResourceUtilization.resource_id)).label('resource_count')
        ).filter(
            ResourceUtilization.start_time >= cutoff
        )
        
        if resource_type:
            query = query.filter(ResourceUtilization.resource_type == resource_type)
        
        metrics = query.group_by(
            ResourceUtilization.resource_type
        ).all()
        
        return {
            metric.resource_type: {
                'avg_utilization': metric.avg_utilization,
                'total_cost': metric.total_cost,
                'resource_count': metric.resource_count
            }
            for metric in metrics
        }
