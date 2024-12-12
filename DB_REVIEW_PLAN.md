# Database Architecture Review Plan

## Overview
This document outlines the systematic review and optimization plan for database interactions across the Flask application and its plugins. The goal is to ensure scalability, connection efficiency, and proper handling of concurrent users.

## Areas of Review

### 1. Core Database Configuration
- Review `config.py` and `.env` settings
- Analyze SQLAlchemy configuration in `app/extensions.py`
- Evaluate connection pooling settings
- Check transaction management

### 2. Main Application Database Patterns
Files to review:
- app/models.py
- app/extensions.py
- app/__init__.py

Focus areas:
- Connection pooling configuration
- Session management
- Model relationships
- Query optimization opportunities
- Transaction handling

### 3. Plugin Database Interactions
Review each plugin's database usage:

#### Critical Plugins (Based on complexity):
1. Projects Plugin
   - Complex models and relationships
   - Migration handling
   - Query patterns

2. Documents Plugin
   - File handling with database records
   - Concurrent access patterns

3. Reports Plugin
   - Query optimization for reporting
   - Data aggregation methods

4. Handoffs Plugin
   - Transaction management
   - State management

#### Other Plugins:
- Oncall
- Profile
- Weblinks
- Dispatch
- Admin

### 4. Migration Management
- Review migration strategy
- Check for potential conflicts
- Analyze index usage
- Evaluate schema evolution

### 5. Performance Optimization Areas
- Connection pooling
- Query optimization
- Proper indexing
- Caching strategies
- N+1 query prevention

## Initial Findings

### Current Configuration Analysis

#### Strengths
1. **Connection Pooling Configuration**
   - Good base configuration with pool_size=30
   - Proper pool recycling (3600s)
   - pool_pre_ping enabled for connection verification
   - LIFO pool usage for reduced thread contention

2. **Database Flexibility**
   - Supports both MariaDB and SQLite
   - Clean configuration separation
   - UTF-8 character set enforcement for MariaDB

3. **Session Management**
   - SQLAlchemy-based sessions
   - Proper session lifetime configuration
   - Signed sessions for security

#### Areas for Improvement

1. **Connection Pool Tuning**
```python
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 30,
    'max_overflow': 10,
    'pool_timeout': 20,
}
```
Recommendations:
- Consider increasing max_overflow for high-traffic scenarios
- Implement connection pool monitoring
- Add connection pool metrics logging

2. **Session Management Enhancement**
```python
# Add to config.py
SQLALCHEMY_ENGINE_OPTIONS.update({
    'pool_pre_ping': True,
    'pool_use_lifo': True,
    'echo_pool': True if DEBUG else False
})
```

3. **Cache Configuration Optimization**
Current:
```python
cache = Cache(config={
    'CACHE_TYPE': 'SimpleCache',
    'CACHE_DEFAULT_TIMEOUT': 300
})
```
Recommended:
```python
cache = Cache(config={
    'CACHE_TYPE': 'redis',  # For production
    'CACHE_KEY_PREFIX': 'portal_',
    'CACHE_REDIS_URL': 'redis://localhost:6379/0',
    'CACHE_DEFAULT_TIMEOUT': 300
})
```

## Plugin-Specific Analysis: Projects

### Critical Findings

1. **Complex Relationship Structure**
   - Multiple many-to-many relationships (watchers, stakeholders, shareholders)
   - Hierarchical task structure with depth limits
   - Task dependencies with circular reference prevention
   - History tracking with JSON storage

2. **Performance Concerns**
   - Heavy use of `lazy='subquery'` which can lead to N+1 queries
   - Multiple relationship loads in to_dict() methods
   - Lack of composite indexes for common queries
   - No bulk loading strategies for task hierarchies

### Optimization Recommendations

1. **Index Optimization**
```python
class Project(db.Model):
    __table_args__ = (
        db.Index('idx_project_status_priority', 'status', 'priority'),
        db.Index('idx_project_created_at', 'created_at'),
        {'mysql_engine': 'InnoDB'}
    )

class Task(db.Model):
    __table_args__ = (
        db.Index('idx_task_project_position', 'project_id', 'position'),
        db.Index('idx_task_status_priority', 'status_id', 'priority_id'),
        db.Index('idx_task_parent_project', 'parent_id', 'project_id'),
        {'mysql_engine': 'InnoDB'}
    )

class Todo(db.Model):
    __table_args__ = (
        db.Index('idx_todo_project_task', 'project_id', 'task_id'),
        db.Index('idx_todo_due_date', 'due_date'),
        {'mysql_engine': 'InnoDB'}
    )
```

2. **Relationship Loading Optimization**
```python
class Project(db.Model):
    # Update relationship loading strategies
    watchers = db.relationship(
        'User',
        secondary=project_watchers,
        lazy='joined',  # Change from subquery
        collection_class=set  # For better performance
    )
    
    @classmethod
    def get_with_relationships(cls, project_id):
        """Optimized project loading with relationships"""
        return cls.query.options(
            db.joinedload(cls.lead),
            db.joinedload(cls.watchers),
            db.joinedload(cls.stakeholders),
            db.selectinload(cls.tasks)  # Use selectinload for collections
        ).get(project_id)
```

3. **Task Hierarchy Optimization**
```python
class Task(db.Model):
    @classmethod
    def get_hierarchy(cls, project_id):
        """Efficiently load task hierarchy"""
        return cls.query.filter_by(project_id=project_id).options(
            db.selectinload(cls.subtasks).selectinload(cls.subtasks),
            db.joinedload(cls.status),
            db.joinedload(cls.priority),
            db.joinedload(cls.assigned_to)
        ).filter_by(parent_id=None).all()
```

## Plugin-Specific Analysis: Documents

### Critical Findings

1. **Content Storage Concerns**
   - Large text content stored directly in database (HTML content)
   - Change history storing full previous content
   - No content compression or chunking strategy
   - Potential for large document sizes impacting performance

2. **Relationship Structure**
   - Many-to-many tag relationships
   - Category relationships with potential for N+1 queries
   - Change history with full content copies

### Optimization Recommendations

1. **Content Storage Optimization**
```python
from sqlalchemy.dialects.mysql import LONGTEXT
from zlib import compress, decompress

class Document(db.Model):
    # Add compressed content storage
    content = db.Column(LONGTEXT, nullable=False)
    is_compressed = db.Column(db.Boolean, default=False)
    
    @property
    def document_content(self):
        """Get document content, handling compression."""
        if self.is_compressed:
            return decompress(self.content.encode()).decode()
        return self.content
    
    @document_content.setter
    def document_content(self, content):
        """Set document content with automatic compression for large content."""
        if len(content) > 1000:  # Compress if content is large
            self.content = compress(content.encode()).decode()
            self.is_compressed = True
        else:
            self.content = content
            self.is_compressed = False
```

2. **Change Tracking Optimization**
```python
class DocumentChange(db.Model):
    # Add diff storage instead of full content
    content_diff = db.Column(db.Text)  # Store diff instead of full content
    
    @classmethod
    def create_change(cls, document, user, change_type, old_content=None):
        """Create change record with optimized diff storage."""
        from difflib import unified_diff
        
        change = cls(
            document_id=document.id,
            changed_by=user.id,
            change_type=change_type
        )
        
        if old_content and change_type == 'update':
            diff = '\n'.join(unified_diff(
                old_content.splitlines(),
                document.content.splitlines(),
                fromfile='previous',
                tofile='current',
                lineterm=''
            ))
            change.content_diff = diff
        
        return change
```

## Plugin-Specific Analysis: Handoffs

### Critical Findings

1. **State Management**
   - Simple status tracking (open/closed)
   - Time-based shift assignments
   - Priority-based organization
   - Temporal data (created_at, closed_at, due_date)

2. **Query Patterns**
   - Frequent status checks
   - Time-range queries for shifts
   - Priority filtering
   - Reporter-based lookups

### Optimization Recommendations

1. **Index Optimization**
```python
class Handoff(db.Model):
    __table_args__ = (
        db.Index('idx_handoff_status_created', 'status', 'created_at'),
        db.Index('idx_handoff_assigned_priority', 'assigned_to', 'priority'),
        db.Index('idx_handoff_reporter_status', 'reporter_id', 'status'),
        db.Index('idx_handoff_due_date', 'due_date'),
        {'mysql_engine': 'InnoDB'}
    )
```

2. **Query Optimization**
```python
class Handoff(db.Model):
    @classmethod
    def get_active_handoffs(cls, shift=None):
        """Optimized query for active handoffs."""
        query = cls.query.options(
            db.load_only(
                'id', 'priority', 'ticket', 'hostname',
                'description', 'due_date', 'status'
            ),
            db.joinedload(cls.reporter_user).load_only('username')
        ).filter(cls.status == 'open')
        
        if shift:
            query = query.filter(cls.assigned_to == shift)
        
        return query.order_by(
            cls.priority.desc(),
            cls.due_date.asc()
        ).all()
```

## Implementation Plan

### Phase 1: Core Optimizations
1. Implement connection pool monitoring
2. Add recommended indexes
3. Update relationship loading strategies
4. Implement caching layer

### Phase 2: Plugin-Specific Optimizations
1. Projects Plugin
   - Optimize task hierarchy loading
   - Implement bulk operations
   - Add caching for project statistics

2. Documents Plugin
   - Implement content compression
   - Convert to diff-based change tracking
   - Add content caching

3. Handoffs Plugin
   - Optimize state transitions
   - Add shift statistics caching
   - Implement archival strategy

### Phase 3: Monitoring and Maintenance
1. Setup query performance monitoring
2. Implement connection pool metrics
3. Add cache hit rate tracking
4. Configure automatic archival processes

## Best Practices Guide

### Query Optimization
```python
# Bad
users = User.query.all()
for user in users:
    print(user.profile.name)

# Good
users = User.query.options(
    db.joinedload(User.profile)
).all()
```

### Transaction Management
```python
from contextlib import contextmanager

@contextmanager
def transaction():
    try:
        yield db.session
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
```

### Connection Management
```python
def get_db_stats():
    """Monitor database connection pool."""
    engine = db.engine
    return {
        'pool_size': engine.pool.size(),
        'checked_in': engine.pool.checkedin(),
        'overflow': engine.pool.overflow(),
        'checked_out': engine.pool.checkedout()
    }
```

## Next Steps

1. Begin implementation of core optimizations
2. Roll out plugin-specific improvements
3. Setup monitoring systems
4. Document best practices for developers
5. Establish regular maintenance procedures

This comprehensive plan provides a clear roadmap for optimizing database performance across the entire application while maintaining data integrity and system reliability.
