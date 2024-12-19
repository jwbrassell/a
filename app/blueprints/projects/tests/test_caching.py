"""Tests for caching functionality."""

import pytest
from datetime import datetime, timedelta
from ..utils.caching import (
    cache,
    cached_project,
    cached_task,
    cached_project_stats,
    invalidate_project_cache,
    invalidate_task_cache,
    CacheManager
)
from ..models import Project, Task, Todo

def test_basic_cache_operations(mock_cache):
    """Test basic cache operations."""
    # Test set and get
    cache.set('test_key', 'test_value')
    assert cache.get('test_key') == 'test_value'
    
    # Test delete
    cache.delete('test_key')
    assert cache.get('test_key') is None
    
    # Test clear
    cache.set('key1', 'value1')
    cache.set('key2', 'value2')
    cache.clear()
    assert cache.get('key1') is None
    assert cache.get('key2') is None

def test_cached_project_decorator(app, db, sample_data, mock_cache):
    """Test cached_project decorator."""
    project = sample_data['project']
    
    @cached_project(timeout=300)
    def get_test_project(project_id):
        return Project.query.get(project_id)
    
    # First call should cache
    result1 = get_test_project(project.id)
    assert result1.id == project.id
    
    # Second call should use cache
    result2 = get_test_project(project.id)
    assert result2.id == project.id
    
    # Verify cache was used
    cache_key = f'project_{project.id}'
    assert cache.get(cache_key) is not None

def test_cached_task_decorator(app, db, sample_data, mock_cache):
    """Test cached_task decorator."""
    task = sample_data['tasks'][0]
    
    @cached_task(timeout=300)
    def get_test_task(task_id):
        return Task.query.get(task_id)
    
    # First call should cache
    result1 = get_test_task(task.id)
    assert result1.id == task.id
    
    # Second call should use cache
    result2 = get_test_task(task.id)
    assert result2.id == task.id
    
    # Verify cache was used
    cache_key = f'task_{task.id}'
    assert cache.get(cache_key) is not None

def test_cached_project_stats(app, db, sample_data, mock_cache):
    """Test cached_project_stats decorator."""
    project = sample_data['project']
    
    @cached_project_stats(timeout=60)
    def get_test_project_stats(project_id):
        project = Project.query.get(project_id)
        return {
            'total_tasks': len(project.tasks),
            'completed_tasks': len([t for t in project.tasks if t.status and t.status.name == 'completed'])
        }
    
    # First call should cache
    stats1 = get_test_project_stats(project.id)
    assert isinstance(stats1, dict)
    
    # Second call should use cache
    stats2 = get_test_project_stats(project.id)
    assert stats2 == stats1
    
    # Verify cache was used
    cache_key = f'project_stats_{project.id}'
    assert cache.get(cache_key) is not None

def test_cache_invalidation(app, db, sample_data, mock_cache):
    """Test cache invalidation."""
    project = sample_data['project']
    task = sample_data['tasks'][0]
    
    # Cache some data
    cache.set(f'project_{project.id}', project.to_dict())
    cache.set(f'project_stats_{project.id}', {'total_tasks': 5})
    cache.set(f'task_{task.id}', task.to_dict())
    
    # Test project cache invalidation
    invalidate_project_cache(project.id)
    assert cache.get(f'project_{project.id}') is None
    assert cache.get(f'project_stats_{project.id}') is None
    
    # Test task cache invalidation
    invalidate_task_cache(task.id, project.id)
    assert cache.get(f'task_{task.id}') is None

def test_cache_manager(app, db, sample_data, mock_cache):
    """Test CacheManager functionality."""
    project = sample_data['project']
    
    # Test warm project cache
    CacheManager.warm_project_cache(project.id)
    assert cache.get(f'project_{project.id}') is not None
    assert cache.get(f'project_stats_{project.id}') is not None
    
    # Test warm task cache
    task = sample_data['tasks'][0]
    CacheManager.warm_task_cache(task.id)
    assert cache.get(f'task_{task.id}') is not None

def test_cache_expiration(app, db, sample_data, mock_cache, monkeypatch):
    """Test cache expiration."""
    project = sample_data['project']
    
    # Mock datetime for testing expiration
    class MockDatetime:
        @classmethod
        def utcnow(cls):
            return datetime(2024, 1, 1, 12, 0)
    
    monkeypatch.setattr('datetime.datetime', MockDatetime)
    
    @cached_project(timeout=300)
    def get_test_project(project_id):
        return Project.query.get(project_id)
    
    # Cache project
    result1 = get_test_project(project.id)
    assert result1.id == project.id
    
    # Advance time beyond timeout
    class MockDatetimeLater:
        @classmethod
        def utcnow(cls):
            return datetime(2024, 1, 1, 12, 10)
    
    monkeypatch.setattr('datetime.datetime', MockDatetimeLater)
    
    # Cache should be expired
    cache_key = f'project_{project.id}'
    assert cache.get(cache_key) is None

def test_cache_race_condition(app, db, sample_data, mock_cache):
    """Test handling of cache race conditions."""
    project = sample_data['project']
    
    def update_project():
        project.name = "Updated Name"
        db.session.commit()
        invalidate_project_cache(project.id)
    
    # Cache project
    cache.set(f'project_{project.id}', project.to_dict())
    
    # Simulate concurrent update
    update_project()
    
    # Get fresh data
    @cached_project(timeout=300)
    def get_test_project(project_id):
        return Project.query.get(project_id)
    
    result = get_test_project(project.id)
    assert result.name == "Updated Name"

def test_cache_memory_usage(app, db, sample_data, mock_cache):
    """Test cache memory usage with large datasets."""
    project = sample_data['project']
    
    # Create large dataset
    large_data = {
        'id': project.id,
        'name': project.name,
        'large_field': 'x' * 1000000  # 1MB of data
    }
    
    # Cache large data
    cache.set(f'project_{project.id}', large_data)
    
    # Verify data is cached correctly
    cached_data = cache.get(f'project_{project.id}')
    assert cached_data['id'] == project.id
    assert len(cached_data['large_field']) == 1000000

def test_cache_key_conflicts(app, db, sample_data, mock_cache):
    """Test handling of cache key conflicts."""
    project = sample_data['project']
    task = sample_data['tasks'][0]
    
    # Cache project and task with similar keys
    cache.set(f'project_{project.id}', project.to_dict())
    cache.set(f'project_{project.id}_task_{task.id}', task.to_dict())
    
    # Verify no key conflicts
    project_data = cache.get(f'project_{project.id}')
    task_data = cache.get(f'project_{project.id}_task_{task.id}')
    
    assert project_data['id'] == project.id
    assert task_data['id'] == task.id
