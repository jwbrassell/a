"""
Metrics collection and processing for admin monitoring dashboard
"""
import psutil
import datetime
from flask import current_app
from sqlalchemy import func
from app.extensions import db
from app.models import User, UserActivity
from .models import (
    SystemMetric, ApplicationMetric, UserMetric,
    FeatureUsage, ResourceMetric
)

class MetricsCollector:
    """Collects and processes various system and application metrics"""
    
    @staticmethod
    def collect_system_metrics():
        """Collect current system metrics"""
        now = datetime.datetime.utcnow()
        metrics = []
        
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        metrics.append(SystemMetric(
            timestamp=now,
            metric_type='cpu_usage',
            value=cpu_percent,
            unit='%'
        ))
        
        # Memory metrics
        memory = psutil.virtual_memory()
        metrics.append(SystemMetric(
            timestamp=now,
            metric_type='memory_usage',
            value=memory.percent,
            unit='%'
        ))
        metrics.append(SystemMetric(
            timestamp=now,
            metric_type='memory_available',
            value=memory.available / (1024 * 1024 * 1024),  # Convert to GB
            unit='GB'
        ))
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        metrics.append(SystemMetric(
            timestamp=now,
            metric_type='disk_usage',
            value=disk.percent,
            unit='%'
        ))
        
        # Save metrics
        db.session.bulk_save_objects(metrics)
        db.session.commit()
        
        return metrics

    @staticmethod
    def collect_application_metrics():
        """Collect application-level metrics"""
        now = datetime.datetime.utcnow()
        metrics = []
        
        # Error rate (last hour)
        hour_ago = now - datetime.timedelta(hours=1)
        total_requests = UserActivity.query.filter(
            UserActivity.timestamp >= hour_ago
        ).count()
        
        error_count = UserActivity.query.filter(
            UserActivity.timestamp >= hour_ago,
            UserActivity.activity.like('%Error%')
        ).count()
        
        if total_requests > 0:
            error_rate = (error_count / total_requests) * 100
            metrics.append(ApplicationMetric(
                timestamp=now,
                metric_type='error_rate',
                value=error_rate,
                unit='%'
            ))
        
        # Active users (last 15 minutes)
        fifteen_mins_ago = now - datetime.timedelta(minutes=15)
        active_users = UserActivity.query.filter(
            UserActivity.timestamp >= fifteen_mins_ago
        ).distinct(UserActivity.user_id).count()
        
        metrics.append(UserMetric(
            timestamp=now,
            metric_type='active_users',
            value=active_users,
            unit='count'
        ))
        
        # Save metrics
        db.session.bulk_save_objects(metrics)
        db.session.commit()
        
        return metrics

    @staticmethod
    def get_feature_metrics(days=1):
        """Get feature usage metrics for the specified number of days"""
        day_ago = datetime.datetime.utcnow() - datetime.timedelta(days=days)
        
        # Most used features
        feature_usage = db.session.query(
            FeatureUsage.feature,
            FeatureUsage.plugin,
            func.count(FeatureUsage.id).label('usage_count'),
            func.avg(FeatureUsage.duration).label('avg_duration')
        ).filter(
            FeatureUsage.timestamp >= day_ago
        ).group_by(
            FeatureUsage.feature,
            FeatureUsage.plugin
        ).all()
        
        return feature_usage

    @staticmethod
    def get_resource_utilization(days=7):
        """Get resource utilization metrics for the specified number of days"""
        period_ago = datetime.datetime.utcnow() - datetime.timedelta(days=days)
        
        # Get aggregated resource metrics
        resources = db.session.query(
            ResourceMetric.resource_type,
            ResourceMetric.category,
            func.sum(ResourceMetric.value).label('total_value')
        ).filter(
            ResourceMetric.timestamp >= period_ago
        ).group_by(
            ResourceMetric.resource_type,
            ResourceMetric.category
        ).all()
        
        return resources

    @staticmethod
    def track_feature_usage(feature, plugin, user_id, duration=None, success=True):
        """Track usage of a specific feature"""
        usage = FeatureUsage(
            timestamp=datetime.datetime.utcnow(),
            feature=feature,
            plugin=plugin,
            user_id=user_id,
            duration=duration,
            success=success
        )
        db.session.add(usage)
        db.session.commit()

    @staticmethod
    def track_resource_usage(resource_type, category, value, unit):
        """Track resource usage"""
        metric = ResourceMetric(
            timestamp=datetime.datetime.utcnow(),
            resource_type=resource_type,
            category=category,
            value=value,
            unit=unit
        )
        db.session.add(metric)
        db.session.commit()

    @staticmethod
    def get_system_metrics_history(hours=24):
        """Get system metrics history for the specified number of hours"""
        period_ago = datetime.datetime.utcnow() - datetime.timedelta(hours=hours)
        
        metrics = SystemMetric.query.filter(
            SystemMetric.timestamp >= period_ago
        ).order_by(SystemMetric.timestamp.desc()).all()
        
        return metrics

    @staticmethod
    def get_application_metrics_history(hours=24):
        """Get application metrics history for the specified number of hours"""
        period_ago = datetime.datetime.utcnow() - datetime.timedelta(hours=hours)
        
        metrics = ApplicationMetric.query.filter(
            ApplicationMetric.timestamp >= period_ago
        ).order_by(ApplicationMetric.timestamp.desc()).all()
        
        return metrics

    @staticmethod
    def get_user_metrics_history(hours=24):
        """Get user metrics history for the specified number of hours"""
        period_ago = datetime.datetime.utcnow() - datetime.timedelta(hours=hours)
        
        metrics = UserMetric.query.filter(
            UserMetric.timestamp >= period_ago
        ).order_by(UserMetric.timestamp.desc()).all()
        
        return metrics

    @staticmethod
    def get_feature_usage_trends(days=30):
        """Get feature usage trends over time"""
        period_ago = datetime.datetime.utcnow() - datetime.timedelta(days=days)
        
        trends = db.session.query(
            FeatureUsage.feature,
            FeatureUsage.plugin,
            func.date(FeatureUsage.timestamp).label('date'),
            func.count(FeatureUsage.id).label('usage_count'),
            func.avg(FeatureUsage.duration).label('avg_duration')
        ).filter(
            FeatureUsage.timestamp >= period_ago
        ).group_by(
            FeatureUsage.feature,
            FeatureUsage.plugin,
            func.date(FeatureUsage.timestamp)
        ).order_by(
            func.date(FeatureUsage.timestamp)
        ).all()
        
        return trends
