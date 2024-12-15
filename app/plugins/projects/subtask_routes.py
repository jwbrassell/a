"""Subtask management routes for the projects plugin."""

from flask import render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app.utils.enhanced_rbac import requires_permission
from app.utils.plugin_base import plugin_error_handler
from . import bp, plugin
from .models import Task, History, ProjectStatus, ProjectPriority, ValidationError
from app.models import User
from app import db

logger = plugin.logger

@bp.route('/tasks/<int:task_id>/subtasks')
@login_required
@requires_permission('projects_access', 'read')
@plugin_error_handler
def list_subtasks(task_id):
    """List all subtasks for a task."""
    try:
        parent_task = Task.query.get_or_404(task_id)
        subtasks = Task.query.filter_by(parent_id=task_id).order_by(Task.position).all()
        
        plugin.log_action('list_subtasks', {
            'task_id': task_id,
            'subtask_count': len(subtasks)
        })
        
        return render_template('projects/tasks/subtasks/list.html',
                            parent_task=parent_task,
                            subtasks=subtasks)
                            
    except Exception as e:
        logger.error(f"Error listing subtasks for task {task_id}: {str(e)}")
        raise

@bp.route('/tasks/<int:task_id>/subtasks/new', methods=['GET', 'POST'])
@login_required
@requires_permission('projects_edit', 'write')
@plugin_error_handler
def create_subtask(task_id):
    """Create a new subtask."""
    try:
        parent_task = Task.query.get_or_404(task_id)
        
        if request.method == 'POST':
            # Create subtask
            subtask = Task(
                project_id=parent_task.project_id,
                parent_id=task_id,
                name=request.form['name'],
                summary=request.form.get('summary'),
                description=request.form.get('description'),
                status_id=request.form.get('status_id'),
                priority_id=request.form.get('priority_id'),
                due_date=request.form.get('due_date'),
                created_by=current_user.username,
                position=request.form.get('position', 0),
                list_position=request.form.get('list_position', 'todo')
            )
            
            # Validate subtask depth
            try:
                subtask.validate_depth()
            except ValidationError as e:
                flash(str(e), 'error')
                return redirect(url_for('projects.create_subtask', task_id=task_id))
            
            # Set assigned user
            assigned_to_id = request.form.get('assigned_to_id')
            if assigned_to_id:
                subtask.assigned_to_id = int(assigned_to_id)
            
            # Add dependencies
            dependency_ids = request.form.getlist('dependencies')
            if dependency_ids:
                dependencies = Task.query.filter(Task.id.in_(dependency_ids)).all()
                subtask.dependencies.extend(dependencies)
                # Validate dependencies
                try:
                    subtask.validate_dependencies()
                except ValidationError as e:
                    flash(str(e), 'error')
                    return redirect(url_for('projects.create_subtask', task_id=task_id))
            
            db.session.add(subtask)
            
            # Add history entry
            history = History(
                entity_type='task',
                project_id=parent_task.project_id,
                task_id=subtask.id,
                action='created',
                details={
                    'name': subtask.name,
                    'parent_task': parent_task.name,
                    'status': subtask.status.name if subtask.status else None,
                    'priority': subtask.priority.name if subtask.priority else None
                },
                created_by=current_user.username,
                user_id=current_user.id
            )
            db.session.add(history)
            
            db.session.commit()
            
            plugin.log_action('create_subtask', {
                'parent_task_id': task_id,
                'subtask_id': subtask.id,
                'subtask_name': subtask.name
            })
            
            flash('Subtask created successfully', 'success')
            return redirect(url_for('projects.view_task', id=subtask.id))
            
        # GET request - show form
        users = User.query.all()
        statuses = ProjectStatus.query.all()
        priorities = ProjectPriority.query.all()
        tasks = Task.query.filter_by(project_id=parent_task.project_id).all()
        
        return render_template('projects/tasks/subtasks/create.html',
                            parent_task=parent_task,
                            users=users,
                            statuses=statuses,
                            priorities=priorities,
                            tasks=tasks)
                            
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating subtask for task {task_id}: {str(e)}")
        flash('Error creating subtask', 'error')
        raise

@bp.route('/tasks/<int:id>/convert', methods=['POST'])
@login_required
@requires_permission('projects_edit', 'write')
@plugin_error_handler
def convert_to_subtask(id):
    """Convert a task to a subtask of another task."""
    try:
        task = Task.query.get_or_404(id)
        parent_id = request.form.get('parent_id')
        
        if not parent_id:
            flash('Parent task is required', 'error')
            return redirect(url_for('projects.view_task', id=id))
            
        # Set new parent
        task.parent_id = int(parent_id)
        
        # Validate depth
        try:
            task.validate_depth()
        except ValidationError as e:
            flash(str(e), 'error')
            return redirect(url_for('projects.view_task', id=id))
        
        # Add history entry
        parent_task = Task.query.get(parent_id)
        history = History(
            entity_type='task',
            project_id=task.project_id,
            task_id=task.id,
            action='updated',
            details={
                'converted_to_subtask': True,
                'parent_task': parent_task.name
            },
            created_by=current_user.username,
            user_id=current_user.id
        )
        db.session.add(history)
        
        db.session.commit()
        
        plugin.log_action('convert_to_subtask', {
            'task_id': id,
            'parent_task_id': parent_id
        })
        
        flash('Task converted to subtask successfully', 'success')
        return redirect(url_for('projects.view_task', id=id))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error converting task {id} to subtask: {str(e)}")
        flash('Error converting task to subtask', 'error')
        raise

@bp.route('/tasks/<int:id>/promote', methods=['POST'])
@login_required
@requires_permission('projects_edit', 'write')
@plugin_error_handler
def promote_to_task(id):
    """Promote a subtask to a top-level task."""
    try:
        task = Task.query.get_or_404(id)
        
        if not task.parent_id:
            flash('Task is already a top-level task', 'error')
            return redirect(url_for('projects.view_task', id=id))
        
        # Store old parent for history
        old_parent = task.parent.name
        
        # Remove parent
        task.parent_id = None
        
        # Add history entry
        history = History(
            entity_type='task',
            project_id=task.project_id,
            task_id=task.id,
            action='updated',
            details={
                'promoted_to_task': True,
                'previous_parent': old_parent
            },
            created_by=current_user.username,
            user_id=current_user.id
        )
        db.session.add(history)
        
        db.session.commit()
        
        plugin.log_action('promote_to_task', {
            'task_id': id
        })
        
        flash('Subtask promoted to task successfully', 'success')
        return redirect(url_for('projects.view_task', id=id))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error promoting subtask {id} to task: {str(e)}")
        flash('Error promoting subtask to task', 'error')
        raise

@bp.route('/tasks/<int:task_id>/subtasks/reorder', methods=['POST'])
@login_required
@requires_permission('projects_edit', 'write')
@plugin_error_handler
def reorder_subtasks(task_id):
    """Update subtask positions."""
    try:
        data = request.get_json()
        if not data or 'subtasks' not in data:
            return jsonify({'error': 'Invalid request data'}), 400
            
        # Get parent task to verify project_id
        parent_task = Task.query.get_or_404(task_id)
        
        # Update subtask positions
        Task.reorder_tasks(parent_task.project_id, data['subtasks'])
        db.session.commit()
        
        plugin.log_action('reorder_subtasks', {
            'parent_task_id': task_id,
            'subtask_count': len(data['subtasks'])
        })
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error reordering subtasks: {str(e)}")
        return jsonify({'error': str(e)}), 500
