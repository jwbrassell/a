"""Tests for monitoring functionality."""

import pytest
import time
from datetime import datetime, timedelta
from ..utils.monitoring import (
    performance_metrics,
    query_tracker,
    monitor_performance,
    monitor_database,
    monitor_cache,
    monitor_api,
    get_performance_report,
    log_slow_operations
)

def test_performance_metrics_recording(mock_monitoring):
    """Test recording of performance metrics."""
    # Record some metrics
    performance_metrics.record('test', 'operation1', 0.5)
    performance_metrics.record('test', 'operation1', 1.0)
    performance_metrics.record('test', 'operation2', 0.3)
    
    # Get metrics
    metrics = performance_metrics.get_metrics()
    
    # Verify metrics
    assert 'test:operation1' in metrics
    assert metrics['test:operation1']['count'] == 2
    assert metrics['test:operation1']['avg_time'] == 0.75
    assert metrics['test:operation2']['count'] == 1
    assert metrics['test:operation2']['avg_time'] == 0.3

def test_query_tracking(mock_monitoring):
    """Test query tracking functionality."""
    # Record some queries
    query_tracker.record_query("SELECT * FROM projects", 0.5)
    query_tracker.record_query("SELECT * FROM tasks", 1.5)
    
    # Get slow queries
    slow_queries = query_tracker.get_slow_queries(threshold=1.0)
    
    # Verify tracking
    assert len(slow_queries) == 1
    assert slow_queries[0]['query'] == "SELECT * FROM tasks"
    assert slow_queries[0]['duration'] == 1.5

def test_monitor_performance_decorator():
    """Test monitor_performance decorator."""
    @monitor_performance('test', 'operation')
    def test_function():
        time.sleep(0.1)
        return "result"
    
    # Clear previous metrics
    performance_metrics.clear()
    
    # Run function
    result = test_function()
    
    # Verify metrics were recorded
    metrics = performance_metrics.get_metrics()
    assert 'test:operation' in metrics
    assert metrics['test:operation']['count'] == 1
    assert metrics['test:operation']['success_rate'] == 100

def test_monitor_performance_decorator_with_error():
    """Test monitor_performance decorator with error."""
    @monitor_performance('test', 'error_operation')
    def error_function():
        time.sleep(0.1)
        raise ValueError("Test error")
    
    # Clear previous metrics
    performance_metrics.clear()
    
    # Run function expecting error
    with pytest.raises(ValueError):
        error_function()
    
    # Verify metrics were recorded with error
    metrics = performance_metrics.get_metrics()
    assert 'test:error_operation' in metrics
    assert metrics['test:error_operation']['count'] == 1
    assert metrics['test:error_operation']['success_rate'] == 0

def test_monitor_database_decorator(app, db, sample_data):
    """Test monitor_database decorator."""
    @monitor_database
    def test_query():
        return db.session.query(sample_data['project'].__class__).all()
    
    # Clear previous metrics
    performance_metrics.clear()
    
    # Run query
    results = test_query()
    
    # Verify metrics were recorded
    metrics = performance_metrics.get_metrics()
    assert any(key.startswith('database:') for key in metrics.keys())

def test_monitor_cache_decorator(mock_cache):
    """Test monitor_cache decorator."""
    @monitor_cache
    def test_cache_operation():
        return mock_cache.get('test_key')
    
    # Clear previous metrics
    performance_metrics.clear()
    
    # Run cache operation
    result = test_cache_operation()
    
    # Verify metrics were recorded
    metrics = performance_metrics.get_metrics()
    assert any(key.startswith('cache:') for key in metrics.keys())

def test_monitor_api_decorator(app, client):
    """Test monitor_api decorator."""
    @app.route('/test-endpoint')
    @monitor_api
    def test_endpoint():
        return {'status': 'success'}
    
    # Clear previous metrics
    performance_metrics.clear()
    
    # Make request
    response = client.get('/test-endpoint')
    
    # Verify metrics were recorded
    metrics = performance_metrics.get_metrics()
    assert any(key.startswith('api:') for key in metrics.keys())

def test_performance_report(mock_monitoring):
    """Test performance report generation."""
    # Record some test data
    performance_metrics.record('api', 'get_project', 0.5)
    performance_metrics.record('database', 'query', 1.5)
    query_tracker.record_query("SELECT * FROM projects", 1.2)
    
    # Generate report
    report = get_performance_report()
    
    # Verify report structure
    assert 'timestamp' in report
    assert 'metrics' in report
    assert 'slow_queries' in report
    assert 'summary' in report
    
    # Verify report content
    assert len(report['metrics']) == 2
    assert len(report['slow_queries']) == 1
    assert report['summary']['total_operations'] > 0

def test_log_slow_operations(caplog):
    """Test logging of slow operations."""
    # Record some slow operations
    performance_metrics.record('test', 'slow_operation', 2.0)
    query_tracker.record_query("SELECT * FROM large_table", 1.5)
    
    # Log slow operations
    log_slow_operations()
    
    # Verify logging
    assert any('Slow operation detected' in record.message for record in caplog.records)
    assert any('Slow queries detected' in record.message for record in caplog.records)

def test_monitoring_memory_usage():
    """Test monitoring memory usage with large datasets."""
    # Record many metrics
    for i in range(1000):
        performance_metrics.record('test', f'operation_{i}', 0.1)
    
    # Record many queries
    for i in range(1000):
        query_tracker.record_query(f"SELECT * FROM table_{i}", 0.1)
    
    # Verify memory usage is reasonable
    metrics = performance_metrics.get_metrics()
    queries = query_tracker.get_slow_queries()
    
    assert len(metrics) <= 1000  # Should have some limit
    assert len(queries) <= 1000  # Should have some limit

def test_concurrent_metric_recording():
    """Test concurrent metric recording."""
    import threading
    
    def record_metrics():
        for i in range(100):
            performance_metrics.record('test', 'concurrent_operation', 0.1)
    
    # Create multiple threads
    threads = [threading.Thread(target=record_metrics) for _ in range(5)]
    
    # Start threads
    for thread in threads:
        thread.start()
    
    # Wait for threads to complete
    for thread in threads:
        thread.join()
    
    # Verify metrics
    metrics = performance_metrics.get_metrics()
    assert metrics['test:concurrent_operation']['count'] == 500

def test_metric_aggregation():
    """Test metric aggregation over time."""
    # Record metrics with different times
    now = datetime.utcnow()
    
    # Record metrics for different time periods
    for i in range(24):
        timestamp = now - timedelta(hours=i)
        performance_metrics.record('test', 'hourly_operation', 0.1, 
                                details={'timestamp': timestamp.isoformat()})
    
    # Get metrics
    metrics = performance_metrics.get_metrics()
    
    # Verify aggregation
    assert metrics['test:hourly_operation']['count'] == 24
    assert len(metrics['test:hourly_operation']['recent_details']) <= 5  # Only keep recent
