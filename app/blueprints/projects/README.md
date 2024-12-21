# Projects Blueprint Migration

This document tracks the conversion of the Projects plugin to a Flask blueprint within our application.

## Overview

The Projects module provides project management functionality including:
- Project creation and management
- Task tracking and dependencies
- Todo lists and checklists
- Comments and activity history
- User assignments and watchers
- Status and priority management

## Dependencies

- Flask-SQLAlchemy
- Flask-Login
- Flask-Migrate
- Flask-WTF
- SQLAlchemy

## Installation

1. Install the package:
```bash
pip install flask-blackfridaylunch-projects
```

2. Initialize the blueprint in your Flask application:
```python
from flask import Flask
from app.blueprints.projects import init_app

app = Flask(__name__)
init_app(app)
```

3. Run database migrations:
```bash
flask db upgrade
```

## Configuration

Configuration can be done through environment variables or by creating a config file:

```python
# config.py
from app.blueprints.projects.config import Config

class ProjectConfig(Config):
    PROJECT_NAME = 'My Project'
    PROJECT_UPLOAD_PATH = 'uploads/projects'
    NOTIFICATION_EMAIL_ENABLED = True
```

### Available Configuration Options

#### Project Settings
- `PROJECT_NAME`: Name of your project
- `PROJECT_UPLOAD_PATH`: Path for file uploads
- `PROJECT_ALLOWED_EXTENSIONS`: Allowed file extensions
- `PROJECT_MAX_CONTENT_LENGTH`: Maximum file size

#### Task Settings
- `TASK_MAX_DEPTH`: Maximum depth for subtasks
- `TASK_ALLOW_CIRCULAR_DEPENDENCIES`: Allow circular task dependencies
- `TASK_DEFAULT_LIST_POSITION`: Default kanban position for new tasks

#### Comment Settings
- `COMMENT_ALLOW_MARKDOWN`: Enable markdown in comments
- `COMMENT_MAX_LENGTH`: Maximum comment length

#### Notification Settings
- `NOTIFICATION_EMAIL_ENABLED`: Enable email notifications
- `NOTIFICATION_WEBSOCKET_ENABLED`: Enable websocket notifications
- `NOTIFICATION_DIGEST_ENABLED`: Enable digest notifications
- `NOTIFICATION_DIGEST_INTERVAL`: Hours between digest notifications

## Migration Checklist

### 1. File Structure Setup ✅
- [x] Verify blueprint directory structure
- [x] Update imports in all files
- [x] Check static and template paths

### 2. Database Models ✅
- [x] Update model imports to use app.extensions.db
- [x] Verify User model relationships
- [x] Add lazy loading optimizations
- [x] Add comprehensive model methods
- [x] Add proper error handling

### 3. Blueprint Configuration ✅
- [x] Move plugin config to app config
- [x] Update blueprint registration
- [x] Configure URL prefix
- [x] Set up template and static folders

### 4. Route Updates ✅
- [x] Update routes/__init__.py with proper blueprint structure
- [x] Add error handlers to blueprint
- [x] Update main_routes.py with improved error handling
- [x] Update project_routes.py with comprehensive features
- [x] Update task_routes.py with improved functionality
- [x] Update comment_routes.py with enhanced features
- [x] Update management_routes.py with improved controls
- [x] Migrate priority management functionality
- [x] Migrate status management functionality
- [x] Migrate subtask management functionality

### 5. Authentication & Authorization ✅
- [x] Integrate with app's login system
- [x] Update permission checks using requires_roles
- [x] Add comprehensive permission utilities
- [x] Add logging for security events

### 6. Template Integration
- [ ] Update base template extends
- [ ] Fix static file references
- [ ] Test all template rendering
- [ ] Verify form handling

### 7. Utility Functions ✅
- [x] Create project_utils.py with core functions
- [x] Create task_utils.py with features
- [x] Create comment_utils.py with features
- [x] Create management_utils.py with features:
  - [x] Permission checks
  - [x] Color validation
  - [x] Activity tracking
  - [x] Usage statistics
  - [x] Bulk operations

### 8. Testing
- [ ] Update test configurations
- [ ] Run model tests
- [ ] Test route functionality
- [ ] Verify user permissions

## Completed Changes

### __init__.py ✅
- [x] Removed plugin initialization code
- [x] Updated blueprint registration
- [x] Added proper error handlers
- [x] Configured default configurations

### models.py ✅
- [x] Updated imports to use app.extensions.db
- [x] Added lazy loading optimizations
- [x] Verified User model relationships
- [x] Added comprehensive model methods

### routes/__init__.py ✅
- [x] Reorganized route imports
- [x] Added blueprint error handlers
- [x] Improved route organization
- [x] Added proper documentation

### main_routes.py ✅
- [x] Updated imports to use blueprint structure
- [x] Added error handling and logging
- [x] Added health check endpoint
- [x] Added dashboard stats endpoint

### project_routes.py ✅
- [x] Updated imports to use blueprint structure
- [x] Added comprehensive error handling
- [x] Added detailed logging
- [x] Added project statistics API
- [x] Improved URL generation
- [x] Added security checks

### task_routes.py ✅
- [x] Updated imports to use blueprint structure
- [x] Added comprehensive error handling
- [x] Added API endpoints for:
  - [x] Task statistics
  - [x] Timeline data
  - [x] Dependencies graph
  - [x] Subtasks management
  - [x] Task search
- [x] Improved permission checks
- [x] Added detailed logging

### comment_routes.py ✅
- [x] Updated imports to use blueprint structure
- [x] Added comprehensive error handling
- [x] Added API endpoints for:
  - [x] Comment search
  - [x] Comment statistics
  - [x] Recent comments
- [x] Added notification system
- [x] Improved permission checks
- [x] Added detailed logging

### management_routes.py ✅
- [x] Updated imports to use blueprint structure
- [x] Added comprehensive error handling
- [x] Added API endpoints for:
  - [x] Status management
  - [x] Priority management
  - [x] Usage statistics
  - [x] Bulk operations
- [x] Added validation checks
- [x] Added activity tracking
- [x] Added detailed logging

### project_utils.py ✅
- [x] Created utility module
- [x] Added permission check functions
- [x] Added statistics calculation
- [x] Added timeline generation
- [x] Added error handling and logging

### task_utils.py ✅
- [x] Created utility module
- [x] Added permission checks
- [x] Added task statistics calculation
- [x] Added timeline generation
- [x] Added dependency graph building
- [x] Added error handling and logging

### comment_utils.py ✅
- [x] Created utility module
- [x] Added permission checks
- [x] Added history tracking
- [x] Added activity tracking
- [x] Added statistics calculation
- [x] Added notification system
- [x] Added error handling and logging

### management_utils.py ✅
- [x] Created utility module
- [x] Added permission checks
- [x] Added color validation
- [x] Added usage statistics
- [x] Added bulk update operations
- [x] Added activity tracking
- [x] Added error handling and logging

### Priority Management Migration ✅
- [x] Moved admin operations to management_routes.py:
  - [x] CRUD operations for priorities
  - [x] Bulk update operations
  - [x] Usage statistics
- [x] Moved project operations to project_routes.py:
  - [x] Update project priority
  - [x] Activity tracking
  - [x] History recording
- [x] Added improved error handling
- [x] Added validation checks
- [x] Added proper logging

### Status Management Migration ✅
- [x] Moved admin operations to management_routes.py:
  - [x] CRUD operations for statuses
  - [x] Bulk update operations
  - [x] Usage statistics
- [x] Moved project operations to project_routes.py:
  - [x] Update project status
  - [x] Activity tracking
  - [x] History recording
- [x] Added improved error handling
- [x] Added validation checks
- [x] Added proper logging

### subtask_routes.py ✅
- [x] Updated imports to use blueprint structure
- [x] Added comprehensive error handling
- [x] Added API endpoints for:
  - [x] Subtask CRUD operations
  - [x] Subtask history
  - [x] Subtask comments
  - [x] Subtask management
- [x] Added permission checks
- [x] Added activity tracking
- [x] Added detailed logging

### subtask_utils.py ✅
- [x] Created utility module
- [x] Added permission checks
- [x] Added data validation
- [x] Added history tracking
- [x] Added activity tracking
- [x] Added change management
- [x] Added error handling and logging

## Next Steps

1. Update templates to use new API endpoints:
   - Update status management forms
   - Update priority management forms
   - Update project edit forms
   - Update subtask management forms

2. Test all functionality:
   - Test status management
   - Test priority management
   - Test project updates
   - Test bulk operations
   - Test subtask operations

3. Implement frontend improvements:
   - Add loading states
   - Add error handling
   - Add success notifications
   - Add confirmation dialogs

## Testing Steps

1. Database Migration
```bash
flask db migrate -m "Convert projects to blueprint"
flask db upgrade
```

2. Verify Data
```python
from app.blueprints.projects.models import Project, Task, Comment
Project.query.all()  # Should return existing projects
Task.query.all()     # Should return existing tasks
Comment.query.all()  # Should return existing comments
```

3. Test Routes
- Access /projects/
- Create new project
- Add tasks
- Add subtasks
- Add comments
- Test permissions
- Verify notifications
- Test management functions:
  - Create/edit/delete statuses
  - Create/edit/delete priorities
  - Update project statuses
  - Update project priorities
  - Test bulk operations
  - Manage subtasks

## Known Issues

- None identified yet

## Completion Criteria

- [ ] All database models working
- [ ] Routes accessible and functioning
- [ ] User permissions enforced
- [ ] Templates rendering correctly
- [ ] Static files serving properly
- [ ] All tests passing
- [ ] No console errors
- [ ] Existing data preserved

## Notes

- Added comprehensive error handling and logging
- Added extensive API endpoints for better frontend integration
- Improved security with detailed permission checks
- Added notification system for comments
- Added bulk operations for management functions
- Added usage tracking before deletions
- Successfully migrated priority management functionality
- Successfully migrated status management functionality
- Successfully migrated subtask management functionality
- Next focus will be on template updates and frontend improvements

## API Endpoints

### Project Management
- GET /api/projects/stats - Get project statistics
- PUT /api/projects/{id}/priority - Update project priority
- PUT /api/projects/{id}/status - Update project status

### Status Management
- GET /api/status - Get status details
- POST /api/status/save - Create/update status
- POST /api/status/delete - Delete status
- POST /api/status/bulk-update - Bulk update status references

### Priority Management
- GET /api/priority - Get priority details
- POST /api/priority/save - Create/update priority
- POST /api/priority/delete - Delete priority
- POST /api/priority/bulk-update - Bulk update priority references

### Subtask Management
- GET /api/subtasks/{id} - Get subtask details
- GET /api/subtasks/{id}/history - Get subtask history
- POST /api/tasks/{id}/subtasks - Create new subtask
- PUT /api/subtasks/{id} - Update subtask
- DELETE /api/subtasks/{id} - Delete subtask
- POST /api/subtasks/{id}/comments - Add subtask comment
- GET /api/subtasks/{id}/comments - Get subtask comments

### Comment Management
- GET /api/comments/search - Search comments
- GET /api/comments/{id}/stats - Get comment statistics
- GET /api/comments/recent - Get recent comments

## Frontend Requirements

1. Status Management
   - Status creation form
   - Status edit form
   - Status list view
   - Bulk update interface

2. Priority Management
   - Priority creation form
   - Priority edit form
   - Priority list view
   - Bulk update interface

3. Subtask Management
   - Subtask creation form
   - Subtask edit form
   - Subtask list view
   - Comment interface
   - History view

4. Common Features
   - Loading states
   - Error handling
   - Success notifications
   - Confirmation dialogs
   - Permission-based UI elements

## Directory Structure

```
app/blueprints/projects/
├── __init__.py
├── config.py
├── models.py
├── setup.py
├── MANIFEST.in
├── README.md
├── migrations/
│   └── add_indexes.py
├── routes/
│   ├── __init__.py
│   ├── main_routes.py
│   ├── project_routes.py
│   ├── task_routes.py
│   ├── comment_routes.py
│   ├── management_routes.py
│   └── subtask_routes.py
├── utils/
│   ├── project_utils.py
│   ├── task_utils.py
│   ├── comment_utils.py
│   ├── management_utils.py
│   └── subtask_utils.py
├── static/
│   ├── css/
│   │   └── project.css
│   └── js/
│       ├── project.js
│       ├── tasks.js
│       ├── comments.js
│       ├── todos.js
│       └── shared/
│           └── utils.js
└── templates/
    └── projects/
        ├── create.html
        ├── dashboard.html
        ├── edit.html
        ├── index.html
        ├── list.html
        ├── settings.html
        ├── view.html
        ├── comments/
        ├── components/
        ├── details/
        ├── history/
        ├── layouts/
        ├── tasks/
        └── todos/
