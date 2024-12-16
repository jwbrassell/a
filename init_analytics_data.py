from app import create_app
from app.extensions import db
from app.models.analytics import (
    FeatureUsage, DocumentAnalytics, ProjectMetrics,
    TeamProductivity, ResourceUtilization
)
from datetime import datetime, timedelta
import random

def init_analytics_data():
    """Initialize sample analytics data."""
    app = create_app()
    with app.app_context():
        # Clear existing data
        FeatureUsage.query.delete()
        DocumentAnalytics.query.delete()
        ProjectMetrics.query.delete()
        TeamProductivity.query.delete()
        ResourceUtilization.query.delete()
        db.session.commit()
        
        # Generate data for the last 30 days
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        # Sample features with success rates
        features = {
            'index': 0.91,
            'routes': 0.70,
            'categories': 0.67,
            'roles': 0.78,
            'monitoring': 1.0,
            'users': 1.0,
            'vault_status': 1.0,
            'analytics': 1.0,
            'edit_role': 0.60,
            'new_route': 0.75
        }
        
        # Generate feature usage data
        for day in range(31):
            current_date = start_date + timedelta(days=day)
            for feature_name, success_rate in features.items():
                # Generate 5-15 usage records per feature per day
                for _ in range(random.randint(5, 15)):
                    # Distribute usage throughout the day
                    hour = random.randint(0, 23)
                    minute = random.randint(0, 59)
                    timestamp = current_date.replace(hour=hour, minute=minute)
                    
                    FeatureUsage.record_usage(
                        feature_name=feature_name,
                        user_id=random.randint(1, 10),
                        action=random.choice(['view', 'edit', 'delete']),
                        duration=random.uniform(10, 300),
                        success=random.random() <= success_rate,
                        metadata={'session_id': f'session_{random.randint(1000, 9999)}'}
                    )
        
        # Generate document analytics data
        categories = ['Reports', 'Documentation', 'Policies', 'Templates', 'Archives']
        for day in range(31):
            current_date = start_date + timedelta(days=day)
            for category in categories:
                # Generate 3-8 access records per category per day
                for _ in range(random.randint(3, 8)):
                    # Distribute access throughout the day
                    hour = random.randint(0, 23)
                    minute = random.randint(0, 59)
                    timestamp = current_date.replace(hour=hour, minute=minute)
                    
                    DocumentAnalytics.record_access(
                        document_id=random.randint(1, 50),
                        category=category,
                        user_id=random.randint(1, 10),
                        action=random.choice(['view', 'download', 'edit']),
                        duration=random.uniform(60, 900),
                        metadata={'source': random.choice(['web', 'mobile', 'api'])}
                    )
        
        # Generate project metrics data
        project_metrics = ['completion_rate', 'time_spent', 'bug_count', 'commit_count']
        for day in range(31):
            current_date = start_date + timedelta(days=day)
            for project_id in range(1, 4):
                for metric in project_metrics:
                    # Add some daily variation
                    base_value = random.uniform(50, 80)
                    daily_change = random.uniform(-5, 5)
                    
                    ProjectMetrics.record_metric(
                        project_id=project_id,
                        metric_name=metric,
                        value=max(0, min(100, base_value + daily_change)),
                        metadata={'sprint': f'Sprint {random.randint(1, 5)}'}
                    )
        
        # Generate team productivity data
        productivity_metrics = ['tasks_completed', 'hours_logged', 'code_reviews']
        for day in range(31):
            current_date = start_date + timedelta(days=day)
            for team_id in range(1, 4):
                # Base productivity that improves over time
                base_productivity = 30 + (day / 30) * 20  # Starts at 30, increases to 50
                
                for metric in productivity_metrics:
                    for user_id in range(1, 5):
                        # Add some random variation per user
                        user_productivity = base_productivity + random.uniform(-5, 5)
                        
                        TeamProductivity.record_productivity(
                            team_id=team_id,
                            user_id=user_id,
                            metric_name=metric,
                            value=max(0, user_productivity),
                            metadata={'priority': random.choice(['high', 'medium', 'low'])}
                        )
        
        # Generate resource utilization data
        resource_types = ['server', 'database', 'storage', 'network']
        for day in range(31):
            current_date = start_date + timedelta(days=day)
            for resource_type in resource_types:
                for hour in range(24):
                    timestamp = current_date + timedelta(hours=hour)
                    
                    # Create a daily pattern with peak hours
                    base_utilization = 40  # Base utilization
                    time_factor = abs(hour - 12) / 12  # Peak at midday
                    daily_pattern = 30 * (1 - time_factor)  # Add up to 30% during peak
                    
                    for resource_id in range(1, 4):
                        # Add some random variation per resource
                        utilization = base_utilization + daily_pattern + random.uniform(-5, 5)
                        utilization = max(0, min(100, utilization))
                        
                        ResourceUtilization.record_utilization(
                            resource_id=resource_id,
                            resource_type=resource_type,
                            utilization=utilization,
                            start_time=timestamp,
                            end_time=timestamp + timedelta(hours=1),
                            user_id=random.randint(1, 10),
                            project_id=random.randint(1, 3),
                            cost=utilization * 0.1,  # Cost proportional to utilization
                            metadata={'region': random.choice(['us-east', 'us-west', 'eu-central'])}
                        )
        
        db.session.commit()
        print("Sample analytics data has been initialized successfully!")

if __name__ == '__main__':
    init_analytics_data()
