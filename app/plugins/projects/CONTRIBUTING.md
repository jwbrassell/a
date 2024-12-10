# Contributing to Projects Plugin

Thank you for your interest in contributing to the Projects Plugin! This document provides guidelines and instructions for contributing.

## Development Setup

1. **Clone the Repository**
```bash
git clone <repository-url>
cd <repository-name>
```

2. **Create Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Initialize Database**
```bash
flask db upgrade
```

5. **Run Development Server**
```bash
flask run
```

## Code Style Guidelines

### Python Code

1. **Follow PEP 8**
```python
# Good
def get_project_tasks(project_id):
    """Get all tasks for a project."""
    return Task.query.filter_by(project_id=project_id).all()

# Bad
def getProjectTasks(projectId):
    return Task.query.filter_by(project_id = projectId).all()
```

2. **Use Type Hints**
```python
from typing import List, Optional

def get_task_by_id(task_id: int) -> Optional[Task]:
    return Task.query.get(task_id)
```

3. **Document Functions and Classes**
```python
class Project(db.Model):
    """
    Project model representing a project in the system.
    
    Attributes:
        name (str): The project name
        summary (str): Brief project summary
        description (str): Detailed project description
    """
```

### JavaScript Code

1. **Use Modern JavaScript Features**
```javascript
// Good
const { id, name } = project;
const tasks = tasks.map(task => task.name);

// Bad
var id = project.id;
var name = project.name;
var taskNames = [];
for (var i = 0; i < tasks.length; i++) {
    taskNames.push(tasks[i].name);
}
```

2. **Follow Consistent Naming**
```javascript
// Variables and functions: camelCase
const taskManager = {
    currentTaskId: null,
    handleFormSubmit() { }
};

// Classes: PascalCase
class TaskManager {
    constructor() { }
}
```

3. **Use JSDoc Comments**
```javascript
/**
 * Handles task form submission.
 * @param {Event} e - The form submission event
 * @returns {Promise<void>}
 */
async function handleFormSubmit(e) {
    e.preventDefault();
    // Implementation
}
```

### HTML/Templates

1. **Use Semantic HTML**
```html
<!-- Good -->
<article class="task-card">
    <header class="task-header">
        <h2>Task Title</h2>
    </header>
    <main class="task-content">
        <!-- Content -->
    </main>
</article>

<!-- Bad -->
<div class="task-card">
    <div class="task-header">
        <div>Task Title</div>
    </div>
    <div class="task-content">
        <!-- Content -->
    </div>
</div>
```

2. **Follow BEM Naming Convention**
```html
<div class="task">
    <div class="task__header">
        <h2 class="task__title">Task Title</h2>
        <button class="task__button task__button--delete">Delete</button>
    </div>
</div>
```

## Git Workflow

1. **Branch Naming**
```
feature/add-task-filtering
bugfix/fix-todo-deletion
enhancement/improve-task-modal
```

2. **Commit Messages**
```
# Format
<type>(<scope>): <subject>

# Examples
feat(tasks): add task filtering functionality
fix(todos): fix todo deletion in task modal
docs(readme): update installation instructions
```

3. **Pull Request Process**
- Create feature branch from `develop`
- Make changes and commit
- Push branch and create PR
- Address review comments
- Squash commits if needed
- Merge to `develop`

## Testing Guidelines

### Python Tests

1. **Unit Tests**
```python
def test_create_project():
    """Test project creation."""
    project = Project(name="Test Project")
    db.session.add(project)
    db.session.commit()
    
    assert project.id is not None
    assert project.name == "Test Project"
```

2. **Integration Tests**
```python
def test_project_api(client):
    """Test project API endpoints."""
    response = client.post('/projects/create', json={
        'name': 'Test Project',
        'summary': 'Test Summary'
    })
    assert response.status_code == 200
    assert response.json['success'] is True
```

### JavaScript Tests

1. **Unit Tests**
```javascript
describe('TaskManager', () => {
    it('should handle form submission', async () => {
        const form = document.createElement('form');
        const event = new Event('submit');
        await TaskManager.handleFormSubmit(event);
        // Assert expected behavior
    });
});
```

2. **Integration Tests**
```javascript
describe('Task Creation', () => {
    it('should create task and update UI', async () => {
        const response = await createTask({
            name: 'Test Task',
            summary: 'Test Summary'
        });
        // Assert UI updates
    });
});
```

## Documentation Guidelines

1. **Code Documentation**
- Document all public functions and classes
- Explain complex logic
- Include usage examples

2. **API Documentation**
```python
@bp.route('/projects/<int:project_id>', methods=['GET'])
@login_required
@requires_roles('user')
def view_project(project_id):
    """
    Get project details.
    
    Args:
        project_id (int): The project ID
        
    Returns:
        dict: Project details and related data
        
    Raises:
        404: If project not found
        403: If user lacks permission
    """
```

3. **README Updates**
- Keep installation instructions up to date
- Document new features
- Update configuration options

## Review Process

1. **Code Review Checklist**
- [ ] Follows code style guidelines
- [ ] Includes tests
- [ ] Updates documentation
- [ ] No security vulnerabilities
- [ ] Efficient database queries
- [ ] Proper error handling

2. **Review Comments**
- Be constructive and specific
- Explain why changes are needed
- Provide examples when helpful

3. **Review Response**
- Address all comments
- Explain disagreements respectfully
- Update code as needed

## Release Process

1. **Version Numbering**
```
MAJOR.MINOR.PATCH
1.0.0 - Initial release
1.1.0 - New feature
1.1.1 - Bug fix
```

2. **Release Checklist**
- [ ] All tests pass
- [ ] Documentation updated
- [ ] Database migrations tested
- [ ] Change log updated
- [ ] Version bumped

3. **Deployment Steps**
```bash
# 1. Create release branch
git checkout -b release/1.1.0

# 2. Update version
# Update version in __init__.py

# 3. Run tests
pytest

# 4. Create migrations
flask db migrate
flask db upgrade

# 5. Merge to main
git checkout main
git merge release/1.1.0

# 6. Tag release
git tag -a v1.1.0 -m "Version 1.1.0"
```

## Support

- Create issues for bugs
- Use discussions for questions
- Join our community chat

## License

By contributing, you agree that your contributions will be licensed under the project's MIT License.
