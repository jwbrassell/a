"""Task management routes for the projects plugin."""

from flask import render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app.utils.enhanced_rbac import requires_permission
from app.utils.plugin_base import plugin_error_handler
from . import bp, plugin
from .models import Project, Task, History, ProjectStatus, ProjectPriority, ValidationError
from app.models import User
from app import db

logger = plugin.logger

def register_routes(blueprint):
    """Register routes with the provided blueprint."""
    global bp
    bp = blueprint

    @bp.route('/projects/<int:project_id>/tasks')
    @login_required
    @requires_permission('projects_access', 'read')
    @plugin_error_handler
    def list_tasks(project_id):
        """List all tasks for a project."""
        try:
            project = Project.query.get_or_404(project_id)
            tasks = Task.query.filter_by(project_id=project_id, parent_id=None).all()
            
            plugin.log_action('list_tasks', {
                'project_id': project_id,
                'task_count': len(tasks)
            })
            
            return render_template('projects/tasks/list.html',
                                project=project,
                                tasks=tasks)
                                
        except Exception as e:
            logger.error(f"Error listing tasks for project {project_id}: {str(e)}")
            raise

    @bp.route('/projects/<int:project_id>/tasks/new', methods=['GET', 'POST'])
    @login_required
    @requires_permission('projects_edit', 'write')
    @plugin_error_handler
    def create_task(project_id):
        """Create a new task."""
        try:
            project = Project.query.get_or_404(project_id)
            
            if request.method == 'POST':
                # Create task
                task = Task(
                    project_id=project_id,
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
                
                # Set parent task if specified
                parent_id = request.form.get('parent_id')
                if parent_id:
                    task.parent_id = int(parent_id)
                    # Validate task depth
                    try:
                        task.validate_depth()
                    except ValidationError as e:
                        flash(str(e), 'error')
                        return redirect(url_for('projects.create_task', project_id=project_id))
                
                # Set assigned user
                assigned_to_id = request.form.get('assigned_to_id')
                if assigned_to_id:
                    task.assigned_to_id = int(assigned_to_id)
                
                # Add dependencies
                dependency_ids = request.form.getlist('dependencies')
                if dependency_ids:
                    dependencies = Task.query.filter(Task.id.in_(dependency_ids)).all()
                    task.dependencies.extend(dependencies)
                    # Validate dependencies
                    try:
                        task.validate_dependencies()
                    except ValidationError as e:
                        flash(str(e), 'error')
                        return redirect(url_for('projects.create_task', project_id=project_id))
                
                db.session.add(task)
                
                # Add history entry
                history = History(
                    entity_type='task',
                    project_id=project_id,
                    task_id=task.id,
                    action='created',
                    details={
                        'name': task.name,
                        'status': task.status.name if task.status else None,
                        'priority': task.priority.name if task.priority else None
                    },
                    created_by=current_user.username,
                    user_id=current_user.id
                )
                db.session.add(history)
                
                db.session.commit()
                
                plugin.log_action('create_task', {
                    'project_id': project_id,
                    'task_id': task.id,
                    'task_name': task.name
                })
                
                flash('Task created successfully', 'success')
                return redirect(url_for('projects.view_task', id=task.id))
                
            # GET request - show form
            users = User.query.all()
            statuses = ProjectStatus.query.all()
            priorities = ProjectPriority.query.all()
            tasks = Task.query.filter_by(project_id=project_id).all()
            
            return render_template('projects/tasks/create.html',
                                project=project,
                                users=users,
                                statuses=statuses,
                                priorities=priorities,
                                tasks=tasks)
                                
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating task for project {project_id}: {str(e)}")
            flash('Error creating task', 'error')
            raise

    @bp.route('/tasks/<int:id>')
    @login_required
    @requires_permission('projects_access', 'read')
    @plugin_error_handler
    def view_task(id):
        """View task details."""
        try:
            task = Task.query.get_or_404(id)
            
            plugin.log_action('view_task', {
                'project_id': task.project_id,
                'task_id': task.id,
                'task_name': task.name
            })
            
            return render_template('projects/tasks/view.html',
                                task=task)
                                
        except Exception as e:
            logger.error(f"Error viewing task {id}: {str(e)}")
            raise

    @bp.route('/tasks/<int:id>/edit', methods=['GET', 'POST'])
    @login_required
    @requires_permission('projects_edit', 'write')
    @plugin_error_handler
    def edit_task(id):
        """Edit task details."""
        try:
            task = Task.query.get_or_404(id)
            
            if request.method == 'POST':
                # Track changes for history
                changes = {}
                
                # Update basic fields
                for field in ['name', 'summary', 'description', 'due_date', 'position', 'list_position']:
                    new_value = request.form.get(field)
                    old_value = getattr(task, field)
                    if new_value != old_value:
                        changes[field] = {'old': old_value, 'new': new_value}
                        setattr(task, field, new_value)
                
                # Update status
                status_id = request.form.get('status_id')
                if status_id:
                    new_status_id = int(status_id)
                    if new_status_id != task.status_id:
                        changes['status'] = {
                            'old': task.status.name if task.status else None,
                            'new': ProjectStatus.query.get(new_status_id).name
                        }
                        task.status_id = new_status_id
                
                # Update priority
                priority_id = request.form.get('priority_id')
                if priority_id:
                    new_priority_id = int(priority_id)
                    if new_priority_id != task.priority_id:
                        changes['priority'] = {
                            'old': task.priority.name if task.priority else None,
                            'new': ProjectPriority.query.get(new_priority_id).name
                        }
                        task.priority_id = new_priority_id
                
                # Update assigned user
                assigned_to_id = request.form.get('assigned_to_id')
                if assigned_to_id:
                    new_assigned_id = int(assigned_to_id)
                    if new_assigned_id != task.assigned_to_id:
                        changes['assigned_to'] = {
                            'old': task.assigned_to.username if task.assigned_to else None,
                            'new': User.query.get(new_assigned_id).username
                        }
                        task.assigned_to_id = new_assigned_id
                
                # Update dependencies
                dependency_ids = request.form.getlist('dependencies')
                if dependency_ids:
                    dependency_ids = [int(id) for id in dependency_ids]
                    current_ids = [t.id for t in task.dependencies]
                    if set(dependency_ids) != set(current_ids):
                        new_dependencies = Task.query.filter(Task.id.in_(dependency_ids)).all()
                        changes['dependencies'] = {
                            'old': [t.name for t in task.dependencies],
                            'new': [t.name for t in new_dependencies]
                        }
                        task.dependencies = new_dependencies
                        # Validate dependencies
                        try:
                            task.validate_dependencies()
                        except ValidationError as e:
                            flash(str(e), 'error')
                            return redirect(url_for('projects.edit_task', id=task.id))
                
                if changes:
                    # Add history entry
                    history = History(
                        entity_type='task',
                        project_id=task.project_id,
                        task_id=task.id,
                        action='updated',
                        details=changes,
                        created_by=current_user.username,
                        user_id=current_user.id
                    )
                    db.session.add(history)
                    
                    db.session.commit()
                    
                    plugin.log_action('update_task', {
                        'project_id': task.project_id,
                        'task_id': task.id,
                        'task_name': task.name,
                        'changes': list(changes.keys())
                    })
                    
                    flash('Task updated successfully', 'success')
                
                return redirect(url_for('projects.view_task', id=task.id))
                
            # GET request - show form
            users = User.query.all()
            statuses = ProjectStatus.query.all()
            priorities = ProjectPriority.query.all()
            tasks = Task.query.filter_by(project_id=task.project_id).all()
            
            return render_template('projects/tasks/edit.html',
                                task=task,
                                users=users,
                                statuses=statuses,
                                priorities=priorities,
                                tasks=tasks)
                                
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error editing task {id}: {str(e)}")
            flash('Error updating task', 'error')
            raise

    @bp.route('/tasks/<int:id>/delete', methods=['POST'])
    @login_required
    @requires_permission('projects_edit', 'write')
    @plugin_error_handler
    def delete_task(id):
        """Delete a task."""
        try:
            task = Task.query.get_or_404(id)
            project_id = task.project_id
            name = task.name
            
            db.session.delete(task)
            db.session.commit()
            
            plugin.log_action('delete_task', {
                'project_id': project_id,
                'task_id': id,
                'task_name': name
            })
            
            flash('Task deleted successfully', 'success')
            return redirect(url_for('projects.list_tasks', project_id=project_id))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting task {id}: {str(e)}")
            flash('Error deleting task', 'error')
            raise

    @bp.route('/tasks/reorder', methods=['POST'])
    @login_required
    @requires_permission('projects_edit', 'write')
    @plugin_error_handler
    def reorder_tasks():
        """Update task positions."""
        try:
            data = request.get_json()
            if not data or 'tasks' not in data:
                return jsonify({'error': 'Invalid request data'}), 400
                
            project_id = data.get('project_id')
            if not project_id:
                return jsonify({'error': 'Project ID is required'}), 400
                
            # Update task positions
            Task.reorder_tasks(project_id, data['tasks'])
            db.session.commit()
            
            plugin.log_action('reorder_tasks', {
                'project_id': project_id,
                'task_count': len(data['tasks'])
            })
            
            return jsonify({'status': 'success'})
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error reordering tasks: {str(e)}")
            return jsonify({'error': str(e)}), 500
