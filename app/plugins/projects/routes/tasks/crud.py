"""Basic CRUD operations for tasks."""

from flask import jsonify, request
from flask_login import login_required, current_user
from app.utils.rbac import requires_roles
from app.utils.activity_tracking import track_activity
from app.extensions import db
from ...models import Project, Task, ProjectStatus, ProjectPriority, ValidationError, History, Todo, Comment
from app.plugins.projects import bp
from datetime import datetime
import json
from .utils import (
    serialize_date,
    log_task_activity,
    track_task_changes,
    validate_task_data
)

@bp.route('/<int:project_id>/tasks', methods=['GET'])
@login_required
@requires_roles('user')
def get_project_tasks(project_id):
    """Get all tasks for a project"""
    project = Project.query.get_or_404(project_id)
    tasks = Task.query.filter_by(project_id=project_id, parent_id=None).order_by(Task.position).all()
    return jsonify({
        'success': True,
        'tasks': [task.to_dict() for task in tasks]
    })

@bp.route('/<int:project_id>/task', methods=['POST'])
@login_required
@requires_roles('user')
@track_activity
def create_task(project_id):
    """Create a new task for a project"""
    project = Project.query.get_or_404(project_id)
    data = request.get_json()
    
    print("CREATE TASK - Received data:", json.dumps(data, indent=2))
    
    # Validate task data
    errors = validate_task_data(data)
    if errors:
        return jsonify({
            'success': False,
            'message': errors[0]
        }), 400
    
    try:
        # Get status and priority objects
        status = ProjectStatus.query.filter_by(name=data.get('status')).first() if data.get('status') else None
        priority = ProjectPriority.query.filter_by(name=data.get('priority')).first() if data.get('priority') else None
        
        # Create task
        task = Task(
            name=data['name'],
            summary=data.get('summary', ''),
            description=data.get('description', ''),
            status_id=status.id if status else None,
            priority_id=priority.id if priority else None,
            due_date=datetime.strptime(data['due_date'], '%Y-%m-%d').date() if data.get('due_date') else None,
            assigned_to_id=data.get('assigned_to_id'),
            project_id=project_id,
            position=data.get('position', 0),
            list_position=data.get('list_position', 'todo')
        )
        
        # Add task to session
        db.session.add(task)
        db.session.flush()  # This assigns an ID to the task
        
        # Create history entry
        history = History(
            entity_type='task',
            action='created',
            user_id=current_user.id,
            project_id=project_id,
            task_id=task.id,
            details={
                'name': task.name,
                'summary': task.summary,
                'description': task.description,
                'status': status.name if status else None,
                'priority': priority.name if priority else None,
                'due_date': serialize_date(task.due_date),
                'assigned_to_id': task.assigned_to_id
            }
        )
        db.session.add(history)
        
        # Add todos if provided
        print("CREATE TASK - Processing todos:", json.dumps(data.get('todos', []), indent=2))
        if data.get('todos'):
            for todo_data in data['todos']:
                if todo_data.get('description'):  # Only add todos with descriptions
                    todo = Todo(
                        description=todo_data['description'],
                        completed=todo_data.get('completed', False),
                        due_date=datetime.strptime(todo_data['due_date'], '%Y-%m-%d').date() if todo_data.get('due_date') else None,
                        task_id=task.id,  # Only set task_id for task todos
                        assigned_to_id=todo_data.get('assigned_to_id')
                    )
                    print(f"CREATE TASK - Adding todo: {todo.description}")
                    db.session.add(todo)
        
        # Log activity
        log_task_activity(current_user.id, current_user.username, "Created", task.name)
        
        # Commit changes
        db.session.commit()
        
        task_dict = task.to_dict()
        print("CREATE TASK - Task created:", json.dumps(task_dict, indent=2))
        
        return jsonify({
            'success': True,
            'message': 'Task created successfully',
            'task': task_dict
        })
        
    except ValidationError as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        print("CREATE TASK - Error:", str(e))
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error creating task: {str(e)}'
        }), 500

@bp.route('/task/<int:task_id>', methods=['GET'])
@login_required
@requires_roles('user')
def get_task(task_id):
    """Get a specific task"""
    task = Task.query.get_or_404(task_id)
    task_dict = task.to_dict()
    print("GET TASK - Task data:", json.dumps(task_dict, indent=2))
    return jsonify({
        'success': True,
        'task': task_dict
    })

@bp.route('/task/<int:task_id>/comment', methods=['POST'])
@login_required
@requires_roles('user')
def add_task_comment(task_id):
    """Add a comment to a task"""
    task = Task.query.get_or_404(task_id)
    data = request.get_json()
    
    if not data.get('content'):
        return jsonify({
            'success': False,
            'message': 'Comment content is required'
        }), 400
    
    try:
        comment = Comment(
            content=data['content'],
            user_id=current_user.id,
            task_id=task_id
        )
        db.session.add(comment)
        
        # Create history entry
        history = History(
            entity_type='task',
            action='commented',
            user_id=current_user.id,
            project_id=task.project_id,
            task_id=task.id,
            details={'comment': data['content']}
        )
        db.session.add(history)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Comment added successfully',
            'comment': comment.to_dict()
        })
        
    except Exception as e:
        print("ADD COMMENT - Error:", str(e))
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error adding comment: {str(e)}'
        }), 500

@bp.route('/task/<int:task_id>', methods=['PUT'])
@login_required
@requires_roles('user')
@track_activity
def update_task(task_id):
    """Update a task"""
    task = Task.query.get_or_404(task_id)
    data = request.get_json()
    
    print("UPDATE TASK - Received data:", json.dumps(data, indent=2))
    
    # Validate task data
    errors = validate_task_data(data)
    if errors:
        return jsonify({
            'success': False,
            'message': errors[0]
        }), 400
    
    try:
        # Get status and priority objects
        if data.get('status'):
            status = ProjectStatus.query.filter_by(name=data['status']).first()
            task.status_id = status.id if status else None
            
        if data.get('priority'):
            priority = ProjectPriority.query.filter_by(name=data['priority']).first()
            task.priority_id = priority.id if priority else None
        
        # Update basic fields
        task.name = data.get('name', task.name)
        task.summary = data.get('summary', task.summary)
        task.description = data.get('description', task.description)
        task.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date() if data.get('due_date') else None
        task.assigned_to_id = data.get('assigned_to_id')
        task.position = data.get('position', task.position)
        task.list_position = data.get('list_position', task.list_position)
        
        # Create history entry
        history = History(
            entity_type='task',
            action='updated',
            user_id=current_user.id,
            project_id=task.project_id,
            task_id=task.id,
            details=track_task_changes(task, data)
        )
        db.session.add(history)
        
        # Handle deleted todos first
        if data.get('deleted_todos'):
            print("Processing deleted todos:", data['deleted_todos'])
            Todo.query.filter(Todo.id.in_(data['deleted_todos']), Todo.task_id == task.id).delete(synchronize_session=False)
        
        # Update todos
        print("UPDATE TASK - Processing todos:", json.dumps(data.get('todos', []), indent=2))
        if data.get('todos') is not None:
            # Get existing todos for comparison
            existing_todos = Todo.query.filter_by(task_id=task.id).all()
            print(f"UPDATE TASK - Existing todos: {[t.description for t in existing_todos]}")
            
            # Delete existing todos that weren't in the update
            existing_todo_ids = {str(todo.id) for todo in existing_todos}
            updated_todo_ids = {str(todo.get('id')) for todo in data['todos'] if todo.get('id')}
            todos_to_delete = existing_todo_ids - updated_todo_ids - set(data.get('deleted_todos', []))
            if todos_to_delete:
                Todo.query.filter(Todo.id.in_(todos_to_delete), Todo.task_id == task.id).delete(synchronize_session=False)
            
            # Update or create todos
            for todo_data in data['todos']:
                if not todo_data.get('description'):  # Skip todos without descriptions
                    continue
                
                todo_id = todo_data.get('id')
                if todo_id and str(todo_id) in existing_todo_ids:
                    # Update existing todo
                    todo = Todo.query.get(todo_id)
                    if todo and todo.task_id == task.id:  # Only update if it belongs to this task
                        todo.description = todo_data['description']
                        todo.completed = todo_data.get('completed', False)
                        if todo_data.get('due_date'):
                            try:
                                todo.due_date = datetime.strptime(todo_data['due_date'], '%Y-%m-%d').date()
                            except ValueError:
                                print(f"Invalid date format for todo: {todo_data['due_date']}")
                        else:
                            todo.due_date = None
                else:
                    # Create new todo
                    todo = Todo(
                        description=todo_data['description'],
                        completed=todo_data.get('completed', False),
                        due_date=datetime.strptime(todo_data['due_date'], '%Y-%m-%d').date() if todo_data.get('due_date') else None,
                        task_id=task.id,  # Only set task_id for task todos
                        assigned_to_id=todo_data.get('assigned_to_id')
                    )
                    print(f"UPDATE TASK - Adding todo: {todo.description}")
                    db.session.add(todo)
        
        # Log activity
        log_task_activity(current_user.id, current_user.username, "Updated", task.name)
        
        db.session.commit()
        
        task_dict = task.to_dict()
        print("UPDATE TASK - Task updated:", json.dumps(task_dict, indent=2))
        
        return jsonify({
            'success': True,
            'message': 'Task updated successfully',
            'task': task_dict
        })
        
    except ValidationError as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        print("UPDATE TASK - Error:", str(e))
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error updating task: {str(e)}'
        }), 500

@bp.route('/task/<int:task_id>', methods=['DELETE'])
@login_required
@requires_roles('user')
@track_activity
def delete_task(task_id):
    """Delete a task"""
    task = Task.query.get_or_404(task_id)
    task_name = task.name
    
    try:
        # Create history entry
        history = History(
            entity_type='task',
            action='deleted',
            user_id=current_user.id,
            project_id=task.project_id,
            details={'name': task_name}
        )
        db.session.add(history)
        
        # Log activity
        log_task_activity(current_user.id, current_user.username, "Deleted", task_name)
        
        db.session.delete(task)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Task deleted successfully'
        })
        
    except Exception as e:
        print("DELETE TASK - Error:", str(e))
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error deleting task: {str(e)}'
        }), 500
