# Projects Plugin Technical Documentation

## Architecture Overview

The Projects plugin is built using a modular architecture with clear separation of concerns. Here's a detailed breakdown of its implementation:

### Core Components

1. **Plugin Initialization (`plugin.py`)**
   - Handles plugin bootstrapping and configuration
   - Sets up logging with rotation (logs/projects.log)
   - Registers Jinja2 filters and context processors
   - Initializes database migrations
   - Configures caching and monitoring
   - Provides CLI commands for maintenance

2. **Data Models (`models.py`)**
   - Implements SQLAlchemy models with relationships:
     - `Project`: Core project management
     - `Task`: Hierarchical task system
     - `Todo`: Checklist functionality
     - `Comment`: Discussion system
     - `History`: Change tracking
     - `ProjectStatus`/`ProjectPriority`: Configuration entities

3. **Route Organization**
   - Modular routing system split into logical components:
     - `main_routes.py`: Core views and dashboards
     - `project_routes.py`: Project CRUD operations
     - `task_routes.py`: Task management
     - `subtask_routes.py`: Subtask handling
     - `comment_routes.py`: Comment system
     - `management_routes.py`: Administrative functions
     - `priority_routes.py`: Priority management
     - `status_routes.py`: Status management

## Database Schema Details

### Core Tables

```sql
-- Projects
CREATE TABLE project (
    id INTEGER PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    summary VARCHAR(500),
    icon VARCHAR(50),
    description TEXT,
    status VARCHAR(50),
    priority VARCHAR(50),
    percent_complete INTEGER DEFAULT 0,
    created_by VARCHAR(100) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_private BOOLEAN DEFAULT FALSE,
    notify_task_created BOOLEAN DEFAULT TRUE,
    notify_task_completed BOOLEAN DEFAULT TRUE,
    notify_comments BOOLEAN DEFAULT TRUE,
    lead_id INTEGER REFERENCES user(id)
);

-- Tasks
CREATE TABLE task (
    id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES project(id),
    parent_id INTEGER REFERENCES task(id),
    name VARCHAR(200) NOT NULL,
    summary VARCHAR(500),
    description TEXT,
    status_id INTEGER REFERENCES project_status(id),
    priority_id INTEGER REFERENCES project_priority(id),
    due_date DATE,
    created_by VARCHAR(100) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    position INTEGER DEFAULT 0,
    list_position VARCHAR(50) DEFAULT 'todo',
    assigned_to_id INTEGER REFERENCES user(id)
);
```

### Association Tables

```sql
-- Project Team Management
CREATE TABLE project_watchers (
    project_id INTEGER REFERENCES project(id),
    user_id INTEGER REFERENCES user(id),
    PRIMARY KEY (project_id, user_id)
);

CREATE TABLE project_stakeholders (
    project_id INTEGER REFERENCES project(id),
    user_id INTEGER REFERENCES user(id),
    PRIMARY KEY (project_id, user_id)
);

CREATE TABLE project_shareholders (
    project_id INTEGER REFERENCES project(id),
    user_id INTEGER REFERENCES user(id),
    PRIMARY KEY (project_id, user_id)
);

-- Task Dependencies
CREATE TABLE task_dependencies (
    task_id INTEGER REFERENCES task(id),
    dependency_id INTEGER REFERENCES task(id),
    PRIMARY KEY (task_id, dependency_id)
);
```

## Key Features Implementation

### 1. Task Hierarchy System
```python
class Task(db.Model):
    MAX_DEPTH = 3  # Maximum nesting level
    parent_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    subtasks = db.relationship('Task', backref=db.backref('parent', remote_side=[id]))

    def get_depth(self):
        depth = 0
        current = self
        while current.parent:
            depth += 1
            current = current.parent
        return depth

    def validate_depth(self):
        if self.get_depth() >= self.MAX_DEPTH:
            raise ValidationError(f"Maximum task depth of {self.MAX_DEPTH} exceeded")
```

### 2. Dependency Management
```python
class Task(db.Model):
    dependencies = db.relationship(
        'Task', secondary=task_dependencies,
        primaryjoin=(task_dependencies.c.task_id == id),
        secondaryjoin=(task_dependencies.c.dependency_id == id),
        backref=db.backref('dependent_tasks', lazy='dynamic'),
        lazy='dynamic'
    )

    def validate_dependencies(self):
        """Prevent circular dependencies"""
        visited = set()
        def check_circular(task):
            if task.id in visited:
                raise ValidationError("Circular dependency detected")
            visited.add(task.id)
            for dep in task.dependencies:
                check_circular(dep)
            visited.remove(task.id)
        check_circular(self)
```

### 3. History Tracking
```python
class History(db.Model):
    entity_type = db.Column(db.String(50))  # 'project', 'task', 'todo'
    action = db.Column(db.String(50))       # 'created', 'updated', 'deleted'
    details = db.Column(db.JSON)            # Stores changes in JSON format
```

## Security Implementation

### 1. Access Control
```python
def can_edit_project(user, project):
    """RBAC implementation for project access"""
    if not user or not project:
        return False
        
    # Admin override
    if any(role.name == 'admin' for role in user.roles):
        return True
        
    # Check route permissions
    mapping = PageRouteMapping.query.filter_by(
        route='projects.edit_project'
    ).first()
    
    if not mapping:
        return True
        
    required_roles = {role.name for role in mapping.allowed_roles}
    user_roles = {role.name for role in user.roles}
    
    return bool(required_roles & user_roles)
```

### 2. Private Projects
```python
class Project(db.Model):
    is_private = db.Column(db.Boolean, default=False)
    roles = db.relationship('Role', secondary=project_roles)
```

## Performance Optimizations

1. **Lazy Loading Relationships**
   ```python
   tasks = db.relationship('Task', lazy=True)
   comments = db.relationship('Comment', lazy=True)
   ```

2. **Efficient Task Reordering**
   ```python
   @classmethod
   def reorder_tasks(cls, project_id, task_positions):
       for position, task_id in enumerate(task_positions):
           cls.query.filter_by(id=task_id, project_id=project_id).update(
               {'position': position}
           )
   ```

3. **Caching Support**
   - Implemented in utils/caching.py
   - Configurable cache backend
   - Automatic cache invalidation on updates

## Integration Points

### 1. Event System
```python
# Available hooks in project lifecycle
project_created
task_updated
todo_completed
```

### 2. API Endpoints
```python
# Project Management
GET    /projects/                # List projects
POST   /projects/create         # Create project
GET    /projects/<id>           # Project details
PUT    /projects/<id>           # Update project
DELETE /projects/<id>           # Delete project

# Task Management
GET    /projects/<id>/tasks     # List tasks
POST   /projects/<id>/tasks     # Create task
PUT    /tasks/<id>              # Update task
DELETE /tasks/<id>              # Delete task

# Todo Management
GET    /tasks/<id>/todos        # List todos
POST   /tasks/<id>/todos        # Create todo
PUT    /todos/<id>              # Update todo
DELETE /todos/<id>              # Delete todo
```

## CLI Commands

```bash
# Database Management
flask projects init_db          # Initialize database tables

# Cache Management
flask projects clear_cache      # Clear all cache entries

# Monitoring
flask projects performance_report  # Generate performance report
```

## Error Handling

```python
class ValidationError(Exception):
    """Custom validation for project operations"""
    pass

# Example usage
def validate_task_creation(task):
    task.validate_depth()        # Check hierarchy depth
    task.validate_dependencies() # Check for circular dependencies
```

## Monitoring and Logging

1. **Rotating File Logger**
   - Location: logs/projects.log
   - Max Size: 1MB
   - Backup Count: 10

2. **Performance Monitoring**
   - Query tracking (when enabled)
   - Performance reporting
   - Cache hit/miss statistics

## Development Guidelines

1. **Adding New Features**
   - Create appropriate models in models.py
   - Add routes in routes/ directory
   - Update documentation
   - Add tests in tests/ directory

2. **Database Migrations**
   - Use Flask-Migrate for schema changes
   - Always provide rollback procedures
   - Test migrations on sample data

3. **Code Style**
   - Follow PEP 8 guidelines
   - Use type hints where appropriate
   - Document complex functions
   - Maintain test coverage

## Testing

```bash
# Run test suite
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_tasks.py

# Run with coverage
coverage run -m pytest
coverage report
