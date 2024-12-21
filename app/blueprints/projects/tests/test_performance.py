"""Performance tests for the projects plugin."""

import pytest
import time
from datetime import datetime, timedelta
from ..models import Project, Task, Todo, Comment, History
from ..utils.monitoring import performance_metrics, query_tracker
from ..utils.caching import cache

def generate_test_data(db, num_projects=5):
    """Generate test data for performance testing"""
    projects = []
    for i in range(num_projects):
        project = Project(
            name=f"Test Project {i}",
            summary=f"Test Summary {i}",
            description=f"Test Description {i}",
            status='active',
            priority='medium'
        )
        db.session.add(project)
        projects.append(project)
    
    # Create tasks for each project
    for project in projects:
        for i in range(10):  # 10 tasks per project
            task = Task(
                name=f"Task {i}",
                description=f"Task Description {i}",
                project=project
            )
            db.session.add(task)
            
            # Create subtasks
            for j in range(3):  # 3 subtasks per task
                subtask = Task(
                    name=f"Subtask {j}",
                    description=f"Subtask Description {j}",
                    project=project,
                    parent=task
                )
                db.session.add(subtask)
            
            # Create todos
            for j in range(5):  # 5 todos per task
                todo = Todo(
                    description=f"Todo {j}",
                    project=project,
                    task=task
                )
                db.session.add(todo)
            
            # Create comments
            for j in range(3):  # 3 comments per task
                comment = Comment(
                    content=f"Comment {j}",
                    project=project,
                    task=task
                )
                db.session.add(comment)
    
    db.session.commit()
    return projects

@pytest.fixture
def test_data(db):
    """Fixture to create test data"""
    return generate_test_data(db)

def test_project_query_performance(db, test_data):
    """Test project query performance"""
    # Clear query tracker
    query_tracker.clear()
    
    start_time = time.time()
    
    # Test basic project query
    projects = Project.query.all()
    
    # Test project with eager loading
    projects = Project.query.options(
        db.joinedload(Project.tasks),
        db.joinedload(Project.lead),
        db.joinedload(Project.watchers)
    ).all()
    
    duration = time.time() - start_time
    
    # Get slow queries
    slow_queries = query_tracker.get_slow_queries(threshold=0.1)
    
    assert duration < 1.0, f"Query took too long: {duration:.2f}s"
    assert len(slow_queries) == 0, f"Found {len(slow_queries)} slow queries"

def test_task_hierarchy_performance(db, test_data):
    """Test task hierarchy query performance"""
    query_tracker.clear()
    
    start_time = time.time()
    
    # Get all tasks with subtasks
    tasks = Task.query.filter_by(parent_id=None).options(
        db.joinedload(Task.subtasks)
    ).all()
    
    duration = time.time() - start_time
    
    # Check query performance
    slow_queries = query_tracker.get_slow_queries(threshold=0.1)
    
    assert duration < 0.5, f"Query took too long: {duration:.2f}s"
    assert len(slow_queries) == 0, f"Found {len(slow_queries)} slow queries"

def test_cache_effectiveness(db, test_data):
    """Test cache effectiveness"""
    # Clear cache
    cache.clear()
    
    project = test_data[0]
    
    # First request (should miss cache)
    start_time = time.time()
    result1 = Project.query.get(project.id)
    first_duration = time.time() - start_time
    
    # Cache the result
    cache.set(f'project_{project.id}', result1.to_dict())
    
    # Second request (should hit cache)
    start_time = time.time()
    result2 = cache.get(f'project_{project.id}')
    second_duration = time.time() - start_time
    
    assert second_duration < first_duration, "Cache not providing performance improvement"
    assert result2 is not None, "Cache miss when should hit"

def test_bulk_operation_performance(db, test_data):
    """Test bulk operation performance"""
    query_tracker.clear()
    
    start_time = time.time()
    
    # Bulk update task status
    Task.query.filter(
        Task.project_id == test_data[0].id
    ).update({
        'status_id': 1
    })
    
    duration = time.time() - start_time
    
    # Check query performance
    slow_queries = query_tracker.get_slow_queries(threshold=0.1)
    
    assert duration < 0.5, f"Bulk update took too long: {duration:.2f}s"
    assert len(slow_queries) == 0, f"Found {len(slow_queries)} slow queries"

def test_history_query_performance(db, test_data):
    """Test history query performance"""
    query_tracker.clear()
    
    project = test_data[0]
    
    # Create some history entries
    for i in range(100):
        history = History(
            entity_type='project',
            action='updated',
            project_id=project.id,
            details={'change': f'Change {i}'}
        )
        db.session.add(history)
    db.session.commit()
    
    start_time = time.time()
    
    # Query history with date filtering
    history = History.query.filter(
        History.project_id == project.id,
        History.created_at >= datetime.utcnow() - timedelta(days=30)
    ).order_by(History.created_at.desc()).all()
    
    duration = time.time() - start_time
    
    # Check query performance
    slow_queries = query_tracker.get_slow_queries(threshold=0.1)
    
    assert duration < 0.5, f"History query took too long: {duration:.2f}s"
    assert len(slow_queries) == 0, f"Found {len(slow_queries)} slow queries"

def test_complex_query_performance(db, test_data):
    """Test complex query performance"""
    query_tracker.clear()
    
    start_time = time.time()
    
    # Complex query with multiple joins and conditions
    results = db.session.query(Project, Task, Comment).\
        join(Task, Project.id == Task.project_id).\
        join(Comment, Task.id == Comment.task_id).\
        filter(Project.status == 'active').\
        filter(Task.parent_id.is_(None)).\
        order_by(Project.created_at.desc()).\
        all()
    
    duration = time.time() - start_time
    
    # Check query performance
    slow_queries = query_tracker.get_slow_queries(threshold=0.1)
    
    assert duration < 1.0, f"Complex query took too long: {duration:.2f}s"
    assert len(slow_queries) == 0, f"Found {len(slow_queries)} slow queries"

def test_index_effectiveness(db, test_data):
    """Test index effectiveness"""
    query_tracker.clear()
    
    # Test queries that should use indexes
    test_queries = [
        (Project.query.filter_by(status='active').all,
         "Project status index not effective"),
        (Task.query.filter_by(project_id=test_data[0].id).all,
         "Task project_id index not effective"),
        (Task.query.filter_by(parent_id=None).all,
         "Task parent_id index not effective"),
        (Todo.query.filter_by(project_id=test_data[0].id).order_by(Todo.order).all,
         "Todo ordering index not effective")
    ]
    
    for query_func, error_message in test_queries:
        start_time = time.time()
        query_func()
        duration = time.time() - start_time
        
        assert duration < 0.1, error_message + f": {duration:.2f}s"

def test_performance_metrics(db, test_data):
    """Test performance metrics collection"""
    performance_metrics.clear()
    
    # Perform some operations
    for i in range(10):
        Project.query.all()
        Task.query.all()
        Todo.query.all()
    
    metrics = performance_metrics.get_metrics()
    
    assert len(metrics) > 0, "No metrics collected"
    for key, data in metrics.items():
        assert data['avg_time'] < 0.1, f"High average time for {key}: {data['avg_time']:.2f}s"
        assert data['success_rate'] > 95, f"Low success rate for {key}: {data['success_rate']}%"
