"""Analytics service for business intelligence features."""

from datetime import datetime, timedelta, date
from typing import Dict, Any, List, Optional
from sqlalchemy import func, and_, desc, extract, case
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
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            # Get daily usage data for each feature
            daily_usage = db.session.query(
                FeatureUsage.feature_name,
                func.date(FeatureUsage.timestamp).label('date'),
                func.count(FeatureUsage.id).label('count'),
                func.avg(FeatureUsage.duration).label('avg_duration'),
                func.sum(case((FeatureUsage.success.is_(True), 1), else_=0)).label('success_count')
            ).filter(
                FeatureUsage.timestamp >= cutoff
            ).group_by(
                FeatureUsage.feature_name,
                func.date(FeatureUsage.timestamp)
            ).all()

            # Organize data by feature
            feature_data = defaultdict(lambda: {
                'feature': '',
                'usage_count': 0,
                'avg_duration': 0,
                'success_count': 0,
                'usage_data': []
            })

            for record in daily_usage:
                feature = feature_data[record.feature_name]
                feature['feature'] = record.feature_name
                feature['usage_count'] = feature.get('usage_count', 0) + record.count
                feature['avg_duration'] = record.avg_duration or 0
                feature['success_count'] = feature.get('success_count', 0) + (record.success_count or 0)
                
                # Convert date to timestamp in milliseconds
                record_date = record.date if isinstance(record.date, date) else datetime.strptime(str(record.date), '%Y-%m-%d').date()
                date_timestamp = int(datetime.combine(record_date, datetime.min.time()).timestamp() * 1000)
                feature['usage_data'].append([date_timestamp, record.count])

            # Get user engagement metrics
            user_metrics = db.session.query(
                func.count(func.distinct(FeatureUsage.user_id)).label('active_users'),
                func.avg(FeatureUsage.duration).label('avg_session_duration')
            ).filter(
                FeatureUsage.timestamp >= cutoff
            ).first()
            
            return {
                'popular_features': list(feature_data.values()),
                'user_engagement': {
                    'active_users': user_metrics.active_users or 0,
                    'avg_session_duration': user_metrics.avg_session_duration or 0
                },
                'period_days': days
            }
        except Exception as e:
            logger.error(f"Error generating feature usage report: {e}")
            return {
                'popular_features': [],
                'user_engagement': {'active_users': 0, 'avg_session_duration': 0},
                'period_days': days
            }

    @staticmethod
    def get_document_analytics_report(days: int = 30) -> Dict[str, Any]:
        """Generate document analytics report."""
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            # Get popular categories
            popular_categories = DocumentAnalytics.get_popular_categories(days=days)
            
            # Get hourly access patterns
            access_patterns = db.session.query(
                extract('hour', DocumentAnalytics.timestamp).label('hour'),
                func.count(DocumentAnalytics.id).label('count')
            ).filter(
                DocumentAnalytics.timestamp >= cutoff
            ).group_by(
                extract('hour', DocumentAnalytics.timestamp)
            ).order_by(
                'hour'
            ).all()
            
            # Get total access count
            total_access = db.session.query(
                func.count(DocumentAnalytics.id)
            ).filter(
                DocumentAnalytics.timestamp >= cutoff
            ).scalar() or 0
            
            return {
                'popular_categories': [
                    {
                        'name': cat.category,
                        'y': cat.access_count,
                        'unique_users': cat.unique_users,
                        'avg_duration': cat.avg_duration
                    }
                    for cat in popular_categories
                ],
                'access_patterns': [
                    {
                        'hour': pattern.hour,
                        'count': pattern.count
                    }
                    for pattern in access_patterns
                ],
                'total_access': total_access,
                'period_days': days
            }
        except Exception as e:
            logger.error(f"Error generating document analytics report: {e}")
            return {
                'popular_categories': [],
                'access_patterns': [],
                'total_access': 0,
                'period_days': days
            }

    @staticmethod
    def get_project_performance_report(project_id: Optional[int] = None,
                                     days: int = 30) -> Dict[str, Any]:
        """Generate project performance report."""
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            # Get daily metrics for each project
            query = db.session.query(
                ProjectMetrics.project_id,
                ProjectMetrics.metric_name,
                func.date(ProjectMetrics.timestamp).label('date'),
                func.avg(ProjectMetrics.value).label('avg_value')
            ).filter(
                ProjectMetrics.timestamp >= cutoff
            )
            
            if project_id:
                query = query.filter(ProjectMetrics.project_id == project_id)
            
            daily_metrics = query.group_by(
                ProjectMetrics.project_id,
                ProjectMetrics.metric_name,
                func.date(ProjectMetrics.timestamp)
            ).all()
            
            # Count active projects
            active_projects = db.session.query(
                func.count(func.distinct(ProjectMetrics.project_id))
            ).filter(
                ProjectMetrics.timestamp >= cutoff
            ).scalar() or 0
            
            # Organize metrics by project
            projects = defaultdict(lambda: defaultdict(list))
            for metric in daily_metrics:
                # Convert date to timestamp in milliseconds
                metric_date = metric.date if isinstance(metric.date, date) else datetime.strptime(str(metric.date), '%Y-%m-%d').date()
                date_timestamp = int(datetime.combine(metric_date, datetime.min.time()).timestamp() * 1000)
                projects[metric.project_id][metric.metric_name].append({
                    'timestamp': date_timestamp,
                    'avg': float(metric.avg_value or 0)
                })
            
            return {
                'projects': dict(projects),
                'active_projects': active_projects,
                'period_days': days
            }
        except Exception as e:
            logger.error(f"Error generating project performance report: {e}")
            return {
                'projects': {},
                'active_projects': 0,
                'period_days': days
            }

    @staticmethod
    def get_team_productivity_report(team_id: Optional[int] = None,
                                   days: int = 30) -> Dict[str, Any]:
        """Generate team productivity report."""
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            # Get team metrics
            metrics = db.session.query(
                TeamProductivity.team_id,
                func.avg(TeamProductivity.value).label('productivity_score'),
                func.count(func.distinct(TeamProductivity.user_id)).label('active_users')
            ).filter(
                TeamProductivity.timestamp >= cutoff
            ).group_by(
                TeamProductivity.team_id
            ).all()
            
            # Calculate trends (comparing to previous period)
            prev_cutoff = cutoff - timedelta(days=days)
            prev_metrics = db.session.query(
                TeamProductivity.team_id,
                func.avg(TeamProductivity.value).label('prev_score')
            ).filter(
                TeamProductivity.timestamp.between(prev_cutoff, cutoff)
            ).group_by(
                TeamProductivity.team_id
            ).all()
            
            prev_scores = {m.team_id: m.prev_score for m in prev_metrics}
            
            teams = {}
            for metric in metrics:
                prev_score = prev_scores.get(metric.team_id, metric.productivity_score)
                if prev_score and prev_score > 0:
                    trend = ((metric.productivity_score - prev_score) / prev_score) * 100
                else:
                    trend = 0
                
                teams[metric.team_id] = {
                    'productivity_score': float(metric.productivity_score or 0),
                    'active_users': metric.active_users or 0,
                    'trend': float(trend)
                }
            
            return {
                'teams': teams,
                'period_days': days
            }
        except Exception as e:
            logger.error(f"Error generating team productivity report: {e}")
            return {
                'teams': {},
                'period_days': days
            }

    @staticmethod
    def get_resource_utilization_report(resource_type: Optional[str] = None,
                                      days: int = 30) -> Dict[str, Any]:
        """Generate resource utilization report."""
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            # Get daily utilization for each resource type
            daily_utilization = db.session.query(
                ResourceUtilization.resource_type,
                func.date(ResourceUtilization.start_time).label('date'),
                func.avg(ResourceUtilization.utilization).label('avg_utilization'),
                func.sum(ResourceUtilization.cost).label('daily_cost')
            ).filter(
                ResourceUtilization.start_time >= cutoff
            )
            
            if resource_type:
                daily_utilization = daily_utilization.filter(
                    ResourceUtilization.resource_type == resource_type
                )
            
            daily_utilization = daily_utilization.group_by(
                ResourceUtilization.resource_type,
                func.date(ResourceUtilization.start_time)
            ).all()
            
            # Calculate overall metrics
            metrics = defaultdict(lambda: {
                'avg_utilization': 0,
                'total_cost': 0,
                'utilization_data': []
            })
            
            total_cost = 0
            total_utilization = []
            
            for record in daily_utilization:
                resource_metrics = metrics[record.resource_type]
                # Convert date to timestamp in milliseconds
                record_date = record.date if isinstance(record.date, date) else datetime.strptime(str(record.date), '%Y-%m-%d').date()
                date_timestamp = int(datetime.combine(record_date, datetime.min.time()).timestamp() * 1000)
                resource_metrics['utilization_data'].append([
                    date_timestamp,
                    float(record.avg_utilization or 0)
                ])
                
                if record.daily_cost:
                    resource_metrics['total_cost'] = (
                        resource_metrics.get('total_cost', 0) + record.daily_cost
                    )
                    total_cost += record.daily_cost
                
                if record.avg_utilization:
                    total_utilization.append(record.avg_utilization)
            
            # Calculate average utilization across all resources
            avg_utilization = (
                sum(total_utilization) / len(total_utilization)
                if total_utilization else 0
            )
            
            return {
                'metrics': dict(metrics),
                'total_cost': float(total_cost),
                'avg_utilization': float(avg_utilization),
                'period_days': days
            }
        except Exception as e:
            logger.error(f"Error generating resource utilization report: {e}")
            return {
                'metrics': {},
                'total_cost': 0,
                'avg_utilization': 0,
                'period_days': days
            }

# Initialize analytics service
analytics_service = AnalyticsService()
