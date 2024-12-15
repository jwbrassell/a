"""Analytics service for business intelligence features."""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import func, and_, desc
from app.extensions import db
from app.models.analytics import (
    FeatureUsage, DocumentAnalytics, ProjectMetrics,
    TeamProductivity, ResourceUtilization
)
import logging
from collections import defaultdict

# Configure logging
logger = logging.getLogger(__name__)

class AnalyticsService:
    """Service for collecting and analyzing business intelligence data."""
    
    @staticmethod
    def record_feature_usage(feature_name: str, user_id: int, action: str = None,
                           duration: float = None, success: bool = True,
                           metadata: Dict = None) -> None:
        """Record feature usage event."""
        try:
            FeatureUsage.record_usage(
                feature_name=feature_name,
                user_id=user_id,
                action=action,
                duration=duration,
                success=success,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Error recording feature usage: {e}")
            db.session.rollback()

    @staticmethod
    def record_document_access(document_id: int, category: str, user_id: int,
                             action: str, duration: float = None,
                             metadata: Dict = None) -> None:
        """Record document access event."""
        try:
            DocumentAnalytics.record_access(
                document_id=document_id,
                category=category,
                user_id=user_id,
                action=action,
                duration=duration,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Error recording document access: {e}")
            db.session.rollback()

    @staticmethod
    def record_project_metric(project_id: int, metric_name: str, value: float,
                            metadata: Dict = None) -> None:
        """Record project metric."""
        try:
            ProjectMetrics.record_metric(
                project_id=project_id,
                metric_name=metric_name,
                value=value,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Error recording project metric: {e}")
            db.session.rollback()

    @staticmethod
    def record_team_productivity(team_id: int, user_id: int, metric_name: str,
                               value: float, metadata: Dict = None) -> None:
        """Record team productivity metric."""
        try:
            TeamProductivity.record_productivity(
                team_id=team_id,
                user_id=user_id,
                metric_name=metric_name,
                value=value,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Error recording team productivity: {e}")
            db.session.rollback()

    @staticmethod
    def record_resource_usage(resource_id: int, resource_type: str,
                            utilization: float, start_time: datetime,
                            user_id: Optional[int] = None,
                            project_id: Optional[int] = None,
                            end_time: Optional[datetime] = None,
                            cost: Optional[float] = None,
                            metadata: Optional[Dict] = None) -> None:
        """Record resource utilization."""
        try:
            ResourceUtilization.record_utilization(
                resource_id=resource_id,
                resource_type=resource_type,
                utilization=utilization,
                start_time=start_time,
                user_id=user_id,
                project_id=project_id,
                end_time=end_time,
                cost=cost,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Error recording resource utilization: {e}")
            db.session.rollback()

    @staticmethod
    def get_feature_usage_report(days: int = 30) -> Dict[str, Any]:
        """Generate feature usage report."""
        try:
            popular_features = FeatureUsage.get_popular_features(days=days)
            
            # Get user engagement metrics
            cutoff = datetime.utcnow() - timedelta(days=days)
            user_metrics = db.session.query(
                func.count(func.distinct(FeatureUsage.user_id)).label('active_users'),
                func.avg(FeatureUsage.duration).label('avg_session_duration')
            ).filter(
                FeatureUsage.timestamp >= cutoff
            ).first()
            
            return {
                'popular_features': [
                    {
                        'feature': feature.feature_name,
                        'usage_count': feature.usage_count,
                        'avg_duration': feature.avg_duration,
                        'success_rate': feature.success_count / feature.usage_count
                    }
                    for feature in popular_features
                ],
                'user_engagement': {
                    'active_users': user_metrics.active_users,
                    'avg_session_duration': user_metrics.avg_session_duration
                },
                'period_days': days
            }
        except Exception as e:
            logger.error(f"Error generating feature usage report: {e}")
            return {}

    @staticmethod
    def get_document_analytics_report(days: int = 30) -> Dict[str, Any]:
        """Generate document analytics report."""
        try:
            popular_categories = DocumentAnalytics.get_popular_categories(days=days)
            
            return {
                'popular_categories': [
                    {
                        'category': cat.category,
                        'access_count': cat.access_count,
                        'unique_users': cat.unique_users,
                        'avg_duration': cat.avg_duration
                    }
                    for cat in popular_categories
                ],
                'period_days': days
            }
        except Exception as e:
            logger.error(f"Error generating document analytics report: {e}")
            return {}

    @staticmethod
    def get_project_performance_report(project_id: Optional[int] = None,
                                     days: int = 30) -> Dict[str, Any]:
        """Generate project performance report."""
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            query = db.session.query(
                ProjectMetrics.project_id,
                ProjectMetrics.metric_name,
                func.avg(ProjectMetrics.value).label('avg_value'),
                func.min(ProjectMetrics.value).label('min_value'),
                func.max(ProjectMetrics.value).label('max_value')
            ).filter(
                ProjectMetrics.timestamp >= cutoff
            )
            
            if project_id:
                query = query.filter(ProjectMetrics.project_id == project_id)
            
            metrics = query.group_by(
                ProjectMetrics.project_id,
                ProjectMetrics.metric_name
            ).all()
            
            # Organize metrics by project
            projects = defaultdict(lambda: defaultdict(dict))
            for metric in metrics:
                projects[metric.project_id][metric.metric_name] = {
                    'avg': metric.avg_value,
                    'min': metric.min_value,
                    'max': metric.max_value
                }
            
            return {
                'projects': dict(projects),
                'period_days': days
            }
        except Exception as e:
            logger.error(f"Error generating project performance report: {e}")
            return {}

    @staticmethod
    def get_team_productivity_report(team_id: Optional[int] = None,
                                   days: int = 30) -> Dict[str, Any]:
        """Generate team productivity report."""
        try:
            if team_id:
                return TeamProductivity.get_team_performance(team_id, days)
            
            # Get metrics for all teams
            cutoff = datetime.utcnow() - timedelta(days=days)
            metrics = db.session.query(
                TeamProductivity.team_id,
                TeamProductivity.metric_name,
                func.avg(TeamProductivity.value).label('avg_value'),
                func.min(TeamProductivity.value).label('min_value'),
                func.max(TeamProductivity.value).label('max_value'),
                func.count(func.distinct(TeamProductivity.user_id)).label('active_users')
            ).filter(
                TeamProductivity.timestamp >= cutoff
            ).group_by(
                TeamProductivity.team_id,
                TeamProductivity.metric_name
            ).all()
            
            # Organize metrics by team
            teams = defaultdict(lambda: defaultdict(dict))
            for metric in metrics:
                teams[metric.team_id][metric.metric_name] = {
                    'avg_value': metric.avg_value,
                    'min_value': metric.min_value,
                    'max_value': metric.max_value,
                    'active_users': metric.active_users
                }
            
            return {
                'teams': dict(teams),
                'period_days': days
            }
        except Exception as e:
            logger.error(f"Error generating team productivity report: {e}")
            return {}

    @staticmethod
    def get_resource_utilization_report(resource_type: Optional[str] = None,
                                      days: int = 30) -> Dict[str, Any]:
        """Generate resource utilization report."""
        try:
            metrics = ResourceUtilization.get_resource_metrics(resource_type, days)
            
            # Get cost analysis
            cutoff = datetime.utcnow() - timedelta(days=days)
            costs = db.session.query(
                ResourceUtilization.resource_type,
                func.sum(ResourceUtilization.cost).label('total_cost'),
                func.avg(ResourceUtilization.cost).label('avg_daily_cost')
            ).filter(
                ResourceUtilization.start_time >= cutoff,
                ResourceUtilization.cost.isnot(None)
            ).group_by(
                ResourceUtilization.resource_type
            ).all()
            
            # Add cost data to metrics
            for cost in costs:
                if cost.resource_type in metrics:
                    metrics[cost.resource_type].update({
                        'total_cost': cost.total_cost,
                        'avg_daily_cost': cost.avg_daily_cost
                    })
            
            return {
                'metrics': metrics,
                'period_days': days
            }
        except Exception as e:
            logger.error(f"Error generating resource utilization report: {e}")
            return {}

# Initialize analytics service
analytics_service = AnalyticsService()
