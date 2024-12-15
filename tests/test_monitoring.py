import unittest
from datetime import datetime, timedelta
from flask import url_for
from app import create_app
from app.extensions import db
from app.models.metrics import Metric, MetricAlert, MetricDashboard
from app.utils.metrics_collector import metrics_collector
from app.models.user import User
from app.models.role import Role
import json

class TestMonitoring(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        
        # Create database tables
        db.create_all()
        
        # Create test user and role
        role = Role(name='admin')
        db.session.add(role)
        
        user = User(
            username='test_admin',
            email='admin@test.com',
            password='test_password',
            roles=[role]
        )
        db.session.add(user)
        db.session.commit()
        
        # Initialize metrics collector
        metrics_collector.init_app(self.app)

    def tearDown(self):
        """Clean up test environment."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def login(self):
        """Helper function to log in as admin."""
        return self.client.post('/login', data={
            'username': 'test_admin',
            'password': 'test_password'
        }, follow_redirects=True)

    def test_metrics_collection(self):
        """Test basic metrics collection."""
        # Record a test metric
        metrics_collector.record_metric(
            name='test_metric',
            value=42.0,
            tags={'type': 'test'},
            metric_type='gauge'
        )
        
        # Verify metric was recorded
        metric = Metric.query.filter_by(name='test_metric').first()
        self.assertIsNotNone(metric)
        self.assertEqual(metric.value, 42.0)
        self.assertEqual(metric.metric_type, 'gauge')

    def test_system_metrics_collection(self):
        """Test system metrics collection."""
        # Collect system metrics
        metrics_collector.collect_system_metrics()
        
        # Verify CPU metrics were collected
        cpu_metric = Metric.query.filter_by(
            name='system_cpu_percent'
        ).first()
        self.assertIsNotNone(cpu_metric)
        
        # Verify memory metrics were collected
        memory_metric = Metric.query.filter_by(
            name='system_memory_percent'
        ).first()
        self.assertIsNotNone(memory_metric)

    def test_metric_alerts(self):
        """Test metric alerts functionality."""
        # Create a test alert
        alert = MetricAlert(
            name='Test Alert',
            metric_name='system_cpu_percent',
            condition='>',
            threshold=90.0,
            duration=300,
            enabled=True
        )
        db.session.add(alert)
        db.session.commit()
        
        # Record a metric that should trigger the alert
        metrics_collector.record_metric(
            name='system_cpu_percent',
            value=95.0,
            tags={'type': 'system'},
            metric_type='gauge'
        )
        
        # Verify alert condition
        self.assertTrue(alert.check_condition(95.0))

    def test_monitoring_dashboard(self):
        """Test monitoring dashboard access."""
        self.login()
        
        # Test dashboard access
        response = self.client.get('/admin/monitoring/')
        self.assertEqual(response.status_code, 200)
        
        # Test health API
        response = self.client.get('/admin/monitoring/api/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('status', data)
        self.assertIn('components', data)

    def test_metric_statistics(self):
        """Test metric statistics calculation."""
        # Record multiple metrics
        for value in [10.0, 20.0, 30.0, 40.0, 50.0]:
            metrics_collector.record_metric(
                name='test_metric',
                value=value,
                tags={'type': 'test'},
                metric_type='gauge'
            )
        
        # Get statistics
        stats = Metric.get_metric_statistics(
            name='test_metric',
            start_time=datetime.utcnow() - timedelta(hours=1)
        )
        
        # Verify statistics
        self.assertEqual(stats['min'], 10.0)
        self.assertEqual(stats['max'], 50.0)
        self.assertEqual(stats['avg'], 30.0)
        self.assertEqual(stats['count'], 5)

    def test_custom_dashboards(self):
        """Test custom dashboard creation and retrieval."""
        self.login()
        
        # Create a test dashboard
        dashboard = MetricDashboard(
            name='Test Dashboard',
            description='Test dashboard description',
            layout={
                'widgets': [
                    {
                        'type': 'chart',
                        'metric': 'system_cpu_percent',
                        'position': {'x': 0, 'y': 0}
                    }
                ]
            },
            created_by_id=1
        )
        db.session.add(dashboard)
        db.session.commit()
        
        # Test dashboard API
        response = self.client.get('/admin/monitoring/api/dashboards')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'Test Dashboard')

    def test_performance_metrics(self):
        """Test performance metrics collection."""
        self.login()
        
        # Make some requests to generate metrics
        for _ in range(5):
            self.client.get('/admin/monitoring/')
        
        # Test performance API
        response = self.client.get('/admin/monitoring/api/performance')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('requests', data)

    def test_user_activity_metrics(self):
        """Test user activity metrics collection."""
        self.login()
        
        # Generate some user activity
        self.client.get('/admin/monitoring/')
        self.client.get('/admin/monitoring/api/health')
        
        # Test user activity API
        response = self.client.get('/admin/monitoring/api/user-activity')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('active_sessions', data)
        self.assertIn('recent_actions', data)

if __name__ == '__main__':
    unittest.main()
