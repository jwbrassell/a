"""Task management routes for the projects plugin."""

from flask import jsonify, request, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.utils.rbac import requires_roles
from app.utils.activity_tracking import track_activity
from app.extensions import db
from app.models import UserActivity, User
from ..models import Project, Task, History, Comment, ProjectStatus, ProjectPriority, Todo
from app.plugins.projects import bp
from datetime import datetime, date

def serialize_date(date_obj):
    """Helper function to serialize date/datetime objects to ISO format strings"""
    if hasattr(date_obj, 'isoformat'):
        return date_obj.isoformat()
    return None

@bp.route('/<int:project_id>/tasks', methods=['GET'])
@login_required
@requires_roles('user')
def get_project_tasks(project_id):
    """Get all tasks for a project"""
    project = Project.query.get_or_404(project_id)
    return jsonify({
        'success': True,
        'tasks': [task.to_dict() for task in project.tasks]
    })

@bp.route('/task/<int:task_id>/view', methods=['GET'])
@login_required
@requires_roles('user')
def view_task(task_id):
    """View a task"""
    task = Task.query.get_or_404(task_id)
    users = User.query.all()
    statuses = ProjectStatus.query.all()
    priorities = ProjectPriority.query.all()
    
    return render_template('projects/tasks/view.html', 
                         task=task,
                         users=users,
                         statuses=statuses,
                         priorities=priorities,
                         can_edit=True)  # TODO: Add proper permission check

@bp.route('/task/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
@requires_roles('user')
@track_activity
def edit_task(task_id):
    """Edit a task"""
    task = Task.query.get_or_404(task_id)
    users = User.query.all()
    statuses = ProjectStatus.query.all()
    priorities = ProjectPriority.query.all()

    if request.method == 'POST':
        # Track changes for history
        changes = {}
        
        # Update basic task fields
        fields = ['name', 'summary', 'description']
        for field in fields:
            if field in request.form:
                new_value = request.form.get(field)
                old_value = getattr(task, field)
                if new_value != str(old_value):
                    changes[field] = {
                        'old': old_value,
                        'new': new_value
                    }
                    setattr(task, field, new_value)

        # Update status
        if 'status' in request.form:
            new_status = ProjectStatus.query.filter_by(name=request.form['status']).first()
            if new_status and task.status_id != new_status.id:
                changes['status'] = {
                    'old': task.status.name if task.status else None,
                    'new': new_status.name
                }
                task.status_id = new_status.id

        # Update priority
        if 'priority' in request.form:
            new_priority = ProjectPriority.query.filter_by(name=request.form['priority']).first()
            if new_priority and task.priority_id != new_priority.id:
                changes['priority'] = {
                    'old': task.priority.name if task.priority else None,
                    'new': new_priority.name
                }
                task.priority_id = new_priority.id

        # Update assigned user
        if 'assigned_to_id' in request.form:
            new_assigned_id = request.form.get('assigned_to_id')
            if new_assigned_id:
                new_assigned_id = int(new_assigned_id)
            if new_assigned_id != task.assigned_to_id:
                changes['assigned_to'] = {
                    'old': task.assigned_to.username if task.assigned_to else None,
                    'new': User.query.get(new_assigned_id).username if new_assigned_id else None
                }
                task.assigned_to_id = new_assigned_id

        # Handle todos
        existing_todos = {todo.id: todo for todo in task.todos}
        updated_todos = []
        todo_changes = []

        # Process todos from form
        todo_index = 0
        while f'todos[{todo_index}][description]' in request.form:
            description = request.form.get(f'todos[{todo_index}][description]')
            completed = request.form.get(f'todos[{todo_index}][completed]') == 'on'
            due_date_str = request.form.get(f'todos[{todo_index}][due_date]')
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else None
            todo_id = request.form.get(f'todos[{todo_index}][id]')

            if todo_id and todo_id.isdigit():
                # Update existing todo
                todo = existing_todos.get(int(todo_id))
                if todo:
                    if (todo.description != description or 
                        todo.completed != completed or 
                        todo.due_date != due_date):
                        todo_changes.append({
                            'action': 'updated',
                            'description': description,
                            'old_description': todo.description
                        })
                    todo.description = description
                    todo.completed = completed
                    todo.due_date = due_date
                    updated_todos.append(todo)
            else:
                # Create new todo
                todo = Todo(
                    description=description,
                    completed=completed,
                    due_date=due_date,
                    task_id=task.id
                )
                todo_changes.append({
                    'action': 'added',
                    'description': description
                })
                db.session.add(todo)
                updated_todos.append(todo)
            
            todo_index += 1

        # Remove deleted todos
        for todo in task.todos:
            if todo not in updated_todos:
                todo_changes.append({
                    'action': 'removed',
                    'description': todo.description
                })
                db.session.delete(todo)

        if todo_changes:
            changes['todos'] = todo_changes

        if changes:
            # Create history entry
            history = History(
                entity_type='task',
                action='updated',
                user_id=current_user.id,
                project_id=task.project_id,
                task_id=task.id,
                details=changes
            )
            task.project.history.append(history)
            
            # Log activity
            activity = UserActivity(
                user_id=current_user.id,
                username=current_user.username,
                activity=f"Updated task: {task.name}"
            )
            db.session.add(activity)
            
            db.session.commit()
            flash('Task updated successfully', 'success')
            return redirect(url_for('projects.view_task', task_id=task.id))

    return render_template('projects/tasks/edit.html', 
                         task=task,
                         users=users,
                         statuses=statuses,
                         priorities=priorities)

@bp.route('/<int:project_id>/task', methods=['POST'])
@login_required
@requires_roles('user')
@track_activity
def create_task(project_id):
    """Create a new task for a project"""
    project = Project.query.get_or_404(project_id)
    data = request.get_json()
    
    # Validate required fields
    if not data.get('name'):
        return jsonify({
            'success': False,
            'message': 'Task name is required'
        }), 400
    
    # Parse due date if provided
    due_date = None
    if data.get('due_date'):
        try:
            due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid due date format. Use YYYY-MM-DD'
            }), 400

    # Get status and priority objects
    status = None
    if data.get('status'):
        status = ProjectStatus.query.filter_by(name=data['status']).first()

    priority = None
    if data.get('priority'):
        priority = ProjectPriority.query.filter_by(name=data['priority']).first()
    
    task = Task(
        name=data['name'],
        description=data.get('description', ''),
        status_id=status.id if status else None,
        priority_id=priority.id if priority else None,
        due_date=due_date,
        assigned_to_id=data.get('assigned_to_id'),
        project_id=project_id
    )
    
    # Create history entry
    history = History(
        entity_type='task',
        action='created',
        user_id=current_user.id,
        project_id=project.id,
        details={
            'name': task.name,
            'description': task.description,
            'status': status.name if status else None,
            'priority': priority.name if priority else None,
            'due_date': serialize_date(task.due_date),
            'assigned_to_id': task.assigned_to_id
        }
    )
    project.history.append(history)
    
    # Log activity
    activity = UserActivity(
        user_id=current_user.id,
        username=current_user.username,
        activity=f"Created task: {task.name} for project: {project.name}"
    )
    
    db.session.add(task)
    db.session.add(activity)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Task created successfully',
        'task': task.to_dict()
    })

@bp.route('/task/<int:task_id>', methods=['GET'])
@login_required
@requires_roles('user')
def get_task(task_id):
    """Get a specific task"""
    try:
        task = Task.query.get(task_id)
        if not task:
            return jsonify({
                'success': False,
                'message': 'Task not found'
            }), 404
            
        # Check if user has access to the project this task belongs to
        if not task.project:
            return jsonify({
                'success': False,
                'message': 'Task has no associated project'
            }), 400
        
        # Get status and priority options
        statuses = ProjectStatus.query.all()
        priorities = ProjectPriority.query.all()
            
        return jsonify({
            'success': True,
            'task': task.to_dict(),
            'statuses': [status.to_dict() for status in statuses],
            'priorities': [priority.to_dict() for priority in priorities]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error loading task: {str(e)}'
        }), 500

@bp.route('/task/<int:task_id>', methods=['PUT'])
@login_required
@requires_roles('user')
@track_activity
def update_task(task_id):
    """Update a task"""
    task = Task.query.get_or_404(task_id)
    data = request.get_json()
    
    # Validate required fields if provided
    if 'name' in data and not data['name']:
        return jsonify({
            'success': False,
            'message': 'Task name cannot be empty'
        }), 400
    
    # Parse due date if provided
    if 'due_date' in data:
        try:
            if isinstance(data['due_date'], str):
                data['due_date'] = datetime.strptime(data['due_date'], '%Y-%m-%d').date() if data['due_date'] else None
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid due date format. Use YYYY-MM-DD'
            }), 400
    
    # Track changes for history
    changes = {}
    
    # Update basic fields
    basic_fields = ['name', 'summary', 'description', 'assigned_to_id']
    for field in basic_fields:
        if field in data:
            old_value = getattr(task, field)
            new_value = data[field]
            if new_value != old_value:
                changes[field] = {
                    'old': old_value,
                    'new': new_value
                }
                setattr(task, field, new_value)

    # Update status
    if 'status' in data:
        new_status = ProjectStatus.query.filter_by(name=data['status']).first()
        if new_status and task.status_id != new_status.id:
            changes['status'] = {
                'old': task.status.name if task.status else None,
                'new': new_status.name
            }
            task.status_id = new_status.id

    # Update priority
    if 'priority' in data:
        new_priority = ProjectPriority.query.filter_by(name=data['priority']).first()
        if new_priority and task.priority_id != new_priority.id:
            changes['priority'] = {
                'old': task.priority.name if task.priority else None,
                'new': new_priority.name
            }
            task.priority_id = new_priority.id
    
    if changes:
        # Create history entry
        history = History(
            entity_type='task',
            action='updated',
            user_id=current_user.id,
            project_id=task.project_id,
            task_id=task.id,
            details=changes
        )
        task.project.history.append(history)
        
        # Log activity
        activity = UserActivity(
            user_id=current_user.id,
            username=current_user.username,
            activity=f"Updated task: {task.name}"
        )
        db.session.add(activity)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Task updated successfully',
        'task': task.to_dict()
    })

@bp.route('/task/<int:task_id>', methods=['DELETE'])
@login_required
@requires_roles('user')
@track_activity
def delete_task(task_id):
    """Delete a task"""
    task = Task.query.get_or_404(task_id)
    project = task.project
    task_name = task.name
    
    # Create history entry
    history = History(
        entity_type='task',
        action='deleted',
        user_id=current_user.id,
        project_id=project.id,
        details={'name': task_name}
    )
    project.history.append(history)
    
    # Log activity
    activity = UserActivity(
        user_id=current_user.id,
        username=current_user.username,
        activity=f"Deleted task: {task_name} from project: {project.name}"
    )
    
    db.session.add(activity)
    db.session.delete(task)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Task deleted successfully'
    })

@bp.route('/task/<int:task_id>/complete', methods=['POST'])
@login_required
@requires_roles('user')
@track_activity
def complete_task(task_id):
    """Mark a task as complete"""
    task = Task.query.get_or_404(task_id)
    completed_status = ProjectStatus.query.filter_by(name='completed').first()
    if completed_status:
        task.status_id = completed_status.id
    
    # Create history entry
    history = History(
        entity_type='task',
        action='completed',
        user_id=current_user.id,
        project_id=task.project_id,
        task_id=task.id,
        details={'status': 'completed'}
    )
    task.project.history.append(history)
    
    # Log activity
    activity = UserActivity(
        user_id=current_user.id,
        username=current_user.username,
        activity=f"Completed task: {task.name}"
    )
    
    db.session.add(activity)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Task marked as complete',
        'task': task.to_dict()
    })

@bp.route('/task/<int:task_id>/comment', methods=['POST'])
@login_required
@requires_roles('user')
@track_activity
def create_task_comment(task_id):
    """Add a comment to a task"""
    task = Task.query.get_or_404(task_id)
    data = request.get_json()
    
    if not data.get('content'):
        return jsonify({
            'success': False,
            'message': 'Comment content is required'
        }), 400
    
    comment = Comment(
        content=data['content'],
        task_id=task_id,
        user_id=current_user.id
    )
    
    # Create history entry
    history = History(
        entity_type='task',
        action='updated',
        user_id=current_user.id,
        project_id=task.project_id,
        task_id=task_id,
        details={'comment_added': data['content'][:50] + '...' if len(data['content']) > 50 else data['content']}
    )
    task.project.history.append(history)
    
    # Log activity
    activity = UserActivity(
        user_id=current_user.id,
        username=current_user.username,
        activity=f"Added comment to task: {task.name}"
    )
    
    db.session.add(comment)
    db.session.add(activity)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Comment added successfully',
        'comment': comment.to_dict()
    })
