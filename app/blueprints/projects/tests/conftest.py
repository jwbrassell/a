"""Test configuration and fixtures."""

import pytest
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from ..plugin import init_plugin
from ..config import TestingConfig
from ..utils.caching import cache
from ..utils.monitoring import performance_metrics, query_tracker

@pytest.fixture
def app():
    """Create and configure a test Flask application."""
    app = Flask(__name__)
    app.config.from_object(TestingConfig)
    
    # Override config for testing
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'CACHE_TYPE': 'simple',
        'ENABLE_QUERY_TRACKING': True,
        'WTF_CSRF_ENABLED': False
    })
    
    # Initialize plugin
    init_plugin(app)
    
    # Create application context
    with app.app_context():
        yield app

@pytest.fixture
def db(app):
    """Create database and tables."""
    from ..models import db
    db.create_all()
    yield db
    db.session.remove()
    db.drop_all()

@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()

@pytest.fixture(autouse=True)
def clear_caches():
    """Clear cache and monitoring data before each test."""
    cache.clear()
    performance_metrics.clear()
    query_tracker.clear()
    yield

@pytest.fixture
def sample_data(db):
    """Create sample data for testing."""
    from ..models import Project, Task, Todo, User, ProjectStatus, ProjectPriority
    
    # Create test user
    user = User(username='testuser', email='test@example.com')
    db.session.add(user)
    
    # Create status and priority
    status = ProjectStatus(name='active', color='success')
    priority = ProjectPriority(name='medium', color='warning')
    db.session.add_all([status, priority])
    
    # Create project
    project = Project(
        name='Test Project',
        summary='Test Summary',
        description='Test Description',
        status='active',
        priority='medium',
        lead=user
    )
    db.session.add(project)
    
    # Create tasks
    tasks = []
    for i in range(3):
        task = Task(
            name=f'Task {i}',
            description=f'Task Description {i}',
            project=project,
            status=status,
            priority=priority,
            assigned_to=user
        )
        tasks.append(task)
        db.session.add(task)
        
        # Create subtasks
        for j in range(2):
            subtask = Task(
                name=f'Subtask {i}.{j}',
                description=f'Subtask Description {i}.{j}',
                project=project,
                parent=task,
                status=status,
                priority=priority,
                assigned_to=user
            )
            db.session.add(subtask)
        
        # Create todos
        for j in range(2):
            todo = Todo(
                description=f'Todo {i}.{j}',
                project=project,
                task=task,
                order=j
            )
            db.session.add(todo)
    
    db.session.commit()
    
    return {
        'user': user,
        'project': project,
        'tasks': tasks,
        'status': status,
        'priority': priority
    }

@pytest.fixture
def mock_cache(monkeypatch):
    """Mock cache for testing."""
    cache_data = {}
    
    def mock_get(key):
        return cache_data.get(key)
    
    def mock_set(key, value, timeout=None):
        cache_data[key] = value
    
    def mock_delete(key):
        cache_data.pop(key, None)
    
    def mock_clear():
        cache_data.clear()
    
    monkeypatch.setattr(cache, 'get', mock_get)
    monkeypatch.setattr(cache, 'set', mock_set)
    monkeypatch.setattr(cache, 'delete', mock_delete)
    monkeypatch.setattr(cache, 'clear', mock_clear)
    
    return cache_data

@pytest.fixture
def mock_monitoring(monkeypatch):
    """Mock monitoring for testing."""
    metrics_data = {}
    queries = []
    
    def mock_record_metric(category, operation, duration, status='success', details=None):
        key = f'{category}:{operation}'
        if key not in metrics_data:
            metrics_data[key] = {
                'count': 0,
                'total_time': 0,
                'success_count': 0
            }
        metrics_data[key]['count'] += 1
        metrics_data[key]['total_time'] += duration
        if status == 'success':
            metrics_data[key]['success_count'] += 1
    
    def mock_record_query(query, duration):
        queries.append({
            'query': str(query),
            'duration': duration
        })
    
    monkeypatch.setattr(performance_metrics, 'record', mock_record_metric)
    monkeypatch.setattr(query_tracker, 'record_query', mock_record_query)
    
    return {
        'metrics': metrics_data,
        'queries': queries
    }

def pytest_configure(config):
    """Configure pytest."""
    # Register markers
    config.addinivalue_line(
        "markers", "slow: mark test as slow to run"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
