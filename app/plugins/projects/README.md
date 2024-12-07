# Projects Plugin

A comprehensive Flask plugin for managing projects, tasks, and team collaboration with full tracking and notification capabilities.

## Implementation Status

### ✅ Phase 1: Core Structure (Completed)
- Database models for Projects, Tasks, Todos, Comments, and History ✓
- Basic routing and views ✓
- Base templates extending base.html ✓
- Navigation system integration ✓

### Plugin Structure
The plugin follows a standardized structure for optimal organization and maintainability:

- `__init__.py`: Contains only blueprint creation and metadata
  ```python
  bp = Blueprint('projects', __name__, 
                template_folder='templates',
                static_folder='static',
                url_prefix='/projects')
  ```

- `routes.py`: Contains all route definitions including:
  - Index route ('/projects/' and '/projects/index')
  - Project management routes
  - Task management routes
  - Todo management routes
  - Comment management routes

This structure ensures proper route registration and navigation functionality, following the same pattern as other plugins like the dispatch tool.

### ✅ Phase 2: Project Features (Completed)
- Project CRUD operations ✓
- Role management system ✓
- Project status workflow ✓
- Project history tracking ✓
- Basic email notifications ✓
- Project overview dashboard ✓

### ✅ Phase 3: Task & Todo System (Completed)
- Task management system ✓
  - Create and edit tasks ✓
  - View detailed task information ✓
  - Task history tracking ✓
  - Task comments ✓
  - Role-based access control ✓
- Todo checklist system ✓
- Task assignment system ✓
- Due date tracking ✓
- Priority management ✓
- Status workflows ✓

### 🚧 Phase 4: Comments & Collaboration (In Progress)
- Comment system implementation
- User mentions
- Rich text editor integration
- File attachment system
- Email notification system
- Activity feeds

### ⏳ Phase 5: History & Reporting (Pending)
- Transaction history system
- Activity tracking
- Report generation
- Dashboard analytics
- Export capabilities

For detailed implementation documentation, see [IMPLEMENTATION.md](IMPLEMENTATION.md)

## Features

### Project Management
- Create and manage projects with detailed information
- Track project status and progress
- Assign project roles:
  - Project Lead
  - Team Members
  - Watchers
  - Stakeholders
  - Shareholders
- Full project history and activity tracking
- Email notifications for project updates

### Task Management
- Create and edit tasks within projects
- Detailed task view with:
  - Task information
  - Status and priority
  - Assignment details
  - Due dates
  - Task history
  - Comments section
- Task properties:
  - Name
  - Description
  - Status (Open, In Progress, Review, Completed)
  - Priority (Low, Medium, High)
  - Assigned User
  - Due Date
  - Creation/Update Dates
- Role-based access control for editing
- Task comments and discussion
- Task history tracking
- Email notifications for task updates

### Todo Management
- Create todo checklists for projects
- Create todo items within tasks
- Track completion status
- Assign responsibilities
- Progress tracking

### Comments & Collaboration
- Comment system on projects and tasks
- Mention users in comments
- Rich text formatting
- File attachments
- Email notifications for mentions

### History & Tracking
- Complete transaction history for:
  - Projects
  - Tasks
  - Subtasks
  - Comments
  - Status Changes
  - Assignment Changes
- Audit trail of all modifications

## Database Models

### Project
- name: Project name
- description: Project description
- status: Current status
- created_at: Creation timestamp
- updated_at: Last update timestamp
- lead_id: Reference to lead user
- team_members: Many-to-many relationship with users
- watchers: Many-to-many relationship with users
- stakeholders: Many-to-many relationship with users
- shareholders: Many-to-many relationship with users

### Task
- project_id: Reference to project
- name: Task name
- description: Task description
- status: Current status (open, in_progress, review, completed)
- priority: Task priority (low, medium, high)
- assigned_to_id: Reference to assigned user
- due_date: Due date
- created_at: Creation timestamp
- updated_at: Last update timestamp

### Todo
- project_id: Optional reference to project
- task_id: Optional reference to task
- description: Todo description
- completed: Completion status
- completed_at: Completion timestamp
- assigned_to_id: Reference to assigned user
- created_at: Creation timestamp

### Comment
- project_id: Optional reference to project
- task_id: Optional reference to task
- user_id: Reference to commenting user
- content: Comment content
- created_at: Creation timestamp
- updated_at: Last update timestamp

### History
- entity_type: Type of entity (Project/Task/Todo)
- entity_id: ID of the entity
- action: Action performed
- user_id: User who performed action
- details: JSON details of changes
- created_at: Timestamp of action

## Required Roles

- `user`: Basic access to view and interact with projects
- `project_lead`: Can create and manage projects
- `admin`: Full system access

## Dependencies

- Flask-SQLAlchemy: Database models
- Flask-Login: Authentication
- Bootstrap 5: UI framework
- Font Awesome 5: Icons
- DataTables: Data display and management
- TinyMCE/Summernote: Rich text editing
- Select2: Enhanced select boxes
- FullCalendar: Due date management
- SweetAlert2: Notifications
- Moment.js: Date handling
- Toastr: User notifications

## Integration Points

- Extends base.html template
- Uses page_content block for main content
- Integrates with navigation system
- Uses existing user authentication
- Leverages existing activity tracking
- Email notification system

## UI Components

### Project Views
- Project listing (DataTables)
- Project details view
- Project creation/edit forms
- Project dashboard
- Role management interface

### Task Views
- Task board (Kanban style)
- Task details modal with:
  - Task information
  - Status and priority badges
  - Assignment details
  - Due date information
  - Task history table
  - Comments section
- Task creation/edit modal with:
  - Task name and description
  - Status selection
  - Priority selection
  - User assignment
  - Due date setting
- Todo checklist interface

### Collaboration Views
- Comment threads
- Activity feeds
- User mention interface
- File attachment handling

## Activity Tracking

- Project creation and updates
- Task management
  - Task creation
  - Status changes
  - Priority updates
  - Assignment changes
  - Due date modifications
- Todo completions
- Comment additions
- Role changes
- Status changes
- Assignment changes

## Email Notifications

Notifications sent for:
- Project role assignments
- Task assignments
- Due date reminders
- Comment mentions
- Status changes
- Important updates

## Error Handling

- Form validation
- Permission checking
- Database transaction management
- File upload validation
- Email sending failures
- User-friendly error messages
- Toastr notifications for user feedback
