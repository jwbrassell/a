# Projects Plugin

A comprehensive project management plugin for Flask applications. This plugin provides functionality for managing projects, tasks, todos, and comments with a modern, responsive interface.

## Features

- **Project Management**
  - Create, edit, and delete projects
  - Track project status and priority
  - Assign project leads
  - Add project-level todos
  - Project history tracking
  - Project comments

- **Task Management**
  - Create and manage tasks within projects
  - Task status and priority tracking
  - Task assignments
  - Task-specific todos
  - Task history tracking
  - Task comments

- **Todo Management**
  - Separate todos for projects and tasks
  - Todo completion tracking
  - Due dates for todos
  - Todo reordering

- **User Interface**
  - Modern, responsive design
  - Dark theme support
  - Rich text editing for descriptions
  - Dynamic updates
  - Toast notifications

## Project Structure

```
app/plugins/projects/
├── __init__.py              # Plugin initialization
├── config.py               # Plugin configuration
├── models.py              # Database models
├── plugin.py             # Plugin setup
├── routes/               # Route handlers
│   ├── __init__.py
│   ├── projects/        # Project-related routes
│   │   ├── crud.py     # Create, Read, Update, Delete operations
│   │   └── utils.py    # Helper functions
│   └── tasks/          # Task-related routes
│       ├── crud.py     # Task CRUD operations
│       └── utils.py    # Task helper functions
├── static/             # Static assets
│   ├── js/
│   │   ├── project.js  # Project management JavaScript
│   │   ├── tasks.js    # Task management JavaScript
│   │   └── todos.js    # Todo management JavaScript
│   └── css/           # Custom styles
└── templates/         # HTML templates
    └── projects/      # Project-related templates
        ├── create.html
        ├── edit.html
        ├── view.html
        └── components/  # Reusable components
```

## Models

### Project Model

```python
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    summary = db.Column(db.String(500))
    description = db.Column(db.Text)
    status = db.Column(db.String(50))
    priority = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    lead_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    tasks = db.relationship('Task', backref='project')
    todos = db.relationship('Todo', backref='project')
    comments = db.relationship('Comment', backref='project')
    history = db.relationship('History', backref='project')
```

### Task Model

```python
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    name = db.Column(db.String(200), nullable=False)
    summary = db.Column(db.String(500))
    description = db.Column(db.Text)
    status_id = db.Column(db.Integer, db.ForeignKey('project_status.id'))
    priority_id = db.Column(db.Integer, db.ForeignKey('project_priority.id'))
    due_date = db.Column(db.Date)
    
    # Relationships
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    todos = db.relationship('Todo', backref='task')
    comments = db.relationship('Comment', backref='task')
    history = db.relationship('History', backref='task')
```

### Todo Model

```python
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    description = db.Column(db.String(500), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    due_date = db.Column(db.Date)
    sort_order = db.Column(db.Integer, default=0)
```

## API Endpoints

### Projects

- `GET /projects/<int:project_id>` - View project details
- `POST /projects/create` - Create a new project
- `PUT /projects/<int:project_id>` - Update project
- `DELETE /projects/<int:project_id>` - Delete project

### Tasks

- `GET /projects/<int:project_id>/tasks` - List project tasks
- `POST /projects/<int:project_id>/task` - Create task
- `GET /projects/task/<int:task_id>` - Get task details
- `PUT /projects/task/<int:task_id>` - Update task
- `DELETE /projects/task/<int:task_id>` - Delete task

### Comments

- `POST /projects/task/<int:task_id>/comment` - Add comment to task
- `POST /projects/<int:project_id>/comment` - Add comment to project

## Frontend Components

### Project Management

The frontend uses vanilla JavaScript organized into modules:

```javascript
// Project management
const projectModule = {
    init() {
        // Initialize project functionality
    },
    saveProject() {
        // Save project changes
    },
    // ... other project methods
};

// Task management
const TaskManager = {
    init() {
        // Initialize task functionality
    },
    handleFormSubmit() {
        // Handle task form submission
    },
    // ... other task methods
};

// Todo management
const todoModule = {
    init() {
        // Initialize todo functionality
    },
    addTodoItem() {
        // Add new todo
    },
    // ... other todo methods
};
```

## Usage Examples

### Creating a Project

```python
# Backend
@bp.route('/create', methods=['POST'])
@login_required
@requires_roles('user')
def create_project():
    data = request.get_json()
    project = Project(
        name=data['name'],
        summary=data.get('summary', ''),
        description=data.get('description', ''),
        status=data.get('status'),
        priority=data.get('priority')
    )
    db.session.add(project)
    db.session.commit()
    return jsonify({'success': True, 'project': project.to_dict()})

# Frontend
async function createProject(data) {
    const response = await fetch('/projects/create', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-TOKEN': getCsrfToken()
        },
        body: JSON.stringify(data)
    });
    return response.json();
}
```

### Adding a Task

```python
# Backend
@bp.route('/<int:project_id>/task', methods=['POST'])
@login_required
def create_task(project_id):
    data = request.get_json()
    task = Task(
        name=data['name'],
        project_id=project_id,
        summary=data.get('summary', ''),
        description=data.get('description', '')
    )
    db.session.add(task)
    db.session.commit()
    return jsonify({'success': True, 'task': task.to_dict()})

# Frontend
async function createTask(projectId, data) {
    const response = await fetch(`/projects/${projectId}/task`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-TOKEN': getCsrfToken()
        },
        body: JSON.stringify(data)
    });
    return response.json();
}
```

## Installation

1. Copy the projects plugin directory to your Flask application's plugins directory
2. Register the plugin in your Flask application:

```python
from flask import Flask
from app.plugins.projects import init_app as init_projects

app = Flask(__name__)
init_projects(app)
```

3. Run database migrations:

```bash
flask db upgrade
```

## Configuration

The plugin can be configured through your Flask application's config:

```python
# config.py
PROJECTS_PER_PAGE = 20
TASKS_PER_PAGE = 50
ENABLE_TASK_NOTIFICATIONS = True
```

## Dependencies

- Flask
- SQLAlchemy
- Flask-Login
- TinyMCE (for rich text editing)
- Bootstrap 5
- Font Awesome
- Toastr (for notifications)

## Security

The plugin implements several security measures:

- CSRF protection on all forms
- Role-based access control
- Input validation and sanitization
- XSS protection
- SQL injection prevention

## Best Practices

1. **Project Organization**
   - Keep projects focused and well-scoped
   - Use clear, descriptive names
   - Maintain up-to-date status and priority

2. **Task Management**
   - Break down large tasks into smaller ones
   - Set realistic due dates
   - Keep task descriptions clear and concise

3. **Todo Usage**
   - Use project todos for high-level items
   - Use task todos for specific implementation steps
   - Keep todos actionable and specific

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - See LICENSE file for details
