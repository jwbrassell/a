from datetime import datetime, timedelta
from flask import (
    render_template, redirect, url_for, flash,
    request, jsonify, current_app
)
from flask_login import login_required, current_user
from app.utils.rbac import requires_roles
from app.utils.activity_tracking import track_activity
from app.extensions import db
from app.models import User, UserActivity
from sqlalchemy.orm import Session
from . import bp
from .models import (
    Project, Task, Todo, Comment, History,
    project_team_members, project_watchers,
    project_stakeholders, project_shareholders
)
from .forms import (
    ProjectForm, TaskForm, TodoForm,
    CommentForm, ProjectSettingsForm
)

import logging
logger = logging.getLogger(__name__)

# Project Routes
@bp.route('/')
@bp.route('/index')
@login_required
@requires_roles('user')
@track_activity
def index():
    """Display list of projects"""
    # Get statistics for dashboard cards
    active_projects = Project.query.filter_by(status='active').count()
    tasks_due_today = Task.query.filter(
        Task.due_date == datetime.utcnow().date(),
        Task.status != 'completed'
    ).count()
    open_tasks = Task.query.filter(
        Task.status != 'completed'
    ).count()
    my_tasks = Task.query.filter_by(
        assigned_to_id=current_user.id,
        status='in_progress'
    ).count()

    return render_template('projects/index.html',
                         active_projects=active_projects,
                         tasks_due_today=tasks_due_today,
                         open_tasks=open_tasks,
                         my_tasks=my_tasks)

@bp.route('/api/projects')
@login_required
@requires_roles('user')
def get_projects():
    """API endpoint for DataTables to fetch project data"""
    # Get query parameters from DataTables
    draw = request.args.get('draw', type=int)
    start = request.args.get('start', type=int)
    length = request.args.get('length', type=int)
    search = request.args.get('search[value]', type=str)
    order_column = request.args.get('order[0][column]', type=int)
    order_dir = request.args.get('order[0][dir]', type=str)

    # Base query
    query = Project.query

    # Apply search if provided
    if search:
        query = query.filter(Project.name.ilike(f'%{search}%'))

    # Get total record count
    total_records = query.count()

    # Apply ordering
    columns = ['name', 'lead_id', 'status', 'team_members', 'tasks', 'created_at']
    if order_column < len(columns):
        column = columns[order_column]
        if hasattr(Project, column):
            if order_dir == 'desc':
                query = query.order_by(getattr(Project, column).desc())
            else:
                query = query.order_by(getattr(Project, column).asc())

    # Apply pagination
    projects = query.offset(start).limit(length).all()

    # Format data for DataTables
    data = []
    for project in projects:
        team_size = len(project.team_members)
        task_count = Task.query.filter_by(project_id=project.id).count()
        
        data.append({
            'name': f'<a href="{url_for("projects.view", project_id=project.id)}">{project.name}</a>',
            'lead': project.lead.name if project.lead else 'Unassigned',
            'status': project.status.title(),
            'team_size': team_size,
            'tasks': task_count,
            'created': project.created_at.strftime('%Y-%m-%d'),
            'actions': f'''
                <div class="btn-group">
                    <a href="{url_for('projects.view', project_id=project.id)}" 
                       class="btn btn-sm btn-info" title="View">
                        <i class="fas fa-eye"></i>
                    </a>
                    <a href="{url_for('projects.settings', project_id=project.id)}" 
                       class="btn btn-sm btn-secondary" title="Settings">
                        <i class="fas fa-cog"></i>
                    </a>
                    <button type="button" class="btn btn-sm btn-danger" 
                            onclick="deleteProject({project.id})" title="Delete">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            '''
        })

    return jsonify({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': total_records,
        'data': data
    })

@bp.route('/create', methods=['GET', 'POST'])
@login_required
@requires_roles('user')
@track_activity
def create():
    """Create a new project"""
    form = ProjectForm()
    users = User.query.all()
    form.lead_id.choices = [(u.id, u.name) for u in users]
    form.team_members.choices = [(u.id, u.name) for u in users]
    form.watchers.choices = [(u.id, u.name) for u in users]
    form.stakeholders.choices = [(u.id, u.name) for u in users]
    form.shareholders.choices = [(u.id, u.name) for u in users]

    if form.validate_on_submit():
        try:
            # Create project with basic info
            project = Project(
                name=form.name.data,
                description=form.description.data,
                status=form.status.data,
                lead_id=form.lead_id.data
            )
            db.session.add(project)
            db.session.flush()  # Get project ID without committing

            # Create SQL statements for association tables
            if form.team_members.data:
                for member_id in form.team_members.data:
                    db.session.execute(
                        project_team_members.insert().values(
                            project_id=project.id, 
                            user_id=member_id
                        )
                    )

            if form.watchers.data:
                for watcher_id in form.watchers.data:
                    db.session.execute(
                        project_watchers.insert().values(
                            project_id=project.id, 
                            user_id=watcher_id
                        )
                    )

            if form.stakeholders.data:
                for stakeholder_id in form.stakeholders.data:
                    db.session.execute(
                        project_stakeholders.insert().values(
                            project_id=project.id, 
                            user_id=stakeholder_id
                        )
                    )

            if form.shareholders.data:
                for shareholder_id in form.shareholders.data:
                    db.session.execute(
                        project_shareholders.insert().values(
                            project_id=project.id, 
                            user_id=shareholder_id
                        )
                    )

            # Create history entry
            history = History(
                entity_type='project',
                action='created',
                user_id=current_user.id,
                project_id=project.id,
                details={
                    'name': project.name,
                    'status': project.status
                }
            )
            db.session.add(history)

            # Log activity
            activity = UserActivity(
                user_id=current_user.id,
                username=current_user.username,
                activity=f"Created new project: {project.name}"
            )
            db.session.add(activity)

            # Commit all changes
            db.session.commit()
            flash('Project created successfully.', 'success')
            return redirect(url_for('projects.view', project_id=project.id))

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating project: {str(e)}")
            flash('Error creating project. Please try again.', 'error')

    return render_template('projects/create.html', form=form)

@bp.route('/<int:project_id>')
@login_required
@requires_roles('user')
@track_activity
def view(project_id):
    """View project details"""
    project = Project.query.get_or_404(project_id)
    users = User.query.all()  # Get users for task/todo assignment
    completed_tasks = Task.query.filter_by(
        project_id=project_id, 
        status='completed'
    ).count()
    due_soon_tasks = Task.query.filter(
        Task.project_id == project_id,
        Task.due_date >= datetime.utcnow(),
        Task.due_date <= datetime.utcnow() + timedelta(days=7)
    ).count()
    overdue_tasks = Task.query.filter(
        Task.project_id == project_id,
        Task.due_date < datetime.utcnow(),
        Task.status != 'completed'
    ).count()

    return render_template('projects/view.html',
                         project=project,
                         users=users,
                         completed_tasks=completed_tasks,
                         due_soon_tasks=due_soon_tasks,
                         overdue_tasks=overdue_tasks)

@bp.route('/tasks/<int:task_id>')
@login_required
@requires_roles('user')
def get_task(task_id):
    """Get task details"""
    task = Task.query.get_or_404(task_id)
    return jsonify({
        'id': task.id,
        'name': task.name,
        'description': task.description,
        'status': task.status,
        'status_class': task.status_class,
        'priority': task.priority,
        'priority_class': task.priority_class,
        'assigned_to': task.assigned_to.name if task.assigned_to else None,
        'assigned_to_id': task.assigned_to_id,
        'due_date': task.due_date.strftime('%Y-%m-%d') if task.due_date else None
    })

@bp.route('/tasks/<int:task_id>', methods=['PUT'])
@login_required
@requires_roles('user')
@track_activity
def update_task(task_id):
    """Update task details"""
    task = Task.query.get_or_404(task_id)
    form = TaskForm()
    users = User.query.all()
    form.assigned_to_id.choices = [(u.id, u.name) for u in users]
    
    if form.validate_on_submit():
        old_status = task.status
        old_assigned = task.assigned_to_id
        
        form.populate_obj(task)
        
        # Create history entry for status change
        if old_status != task.status:
            history = History(
                entity_type='task',
                action='updated',
                user_id=current_user.id,
                project_id=task.project_id,
                task_id=task.id,
                details={
                    'field': 'status',
                    'old': old_status,
                    'new': task.status
                }
            )
            task.history.append(history)
        
        # Create history entry for assignment change
        if old_assigned != task.assigned_to_id:
            history = History(
                entity_type='task',
                action='updated',
                user_id=current_user.id,
                project_id=task.project_id,
                task_id=task.id,
                details={
                    'field': 'assigned_to',
                    'old': User.query.get(old_assigned).name if old_assigned else None,
                    'new': task.assigned_to.name if task.assigned_to else None
                }
            )
            task.history.append(history)
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Task updated successfully'
        })
    
    return jsonify({
        'status': 'error',
        'message': 'Invalid form data',
        'errors': form.errors
    }), 400

@bp.route('/<int:project_id>/settings', methods=['GET', 'POST'])
@login_required
@requires_roles('user')
@track_activity
def settings(project_id):
    """Project settings page"""
    project = Project.query.get_or_404(project_id)
    users = User.query.all()

    if request.method == 'POST':
        form_type = request.form.get('form_type')
        
        if form_type == 'details':
            # Update project details
            project.name = request.form.get('name')
            project.description = request.form.get('description')
            project.status = request.form.get('status')
            
            # Create history entry
            history = History(
                entity_type='project',
                action='updated',
                user_id=current_user.id,
                project_id=project.id,
                details={
                    'fields': ['name', 'description', 'status'],
                    'name': project.name,
                    'status': project.status
                }
            )
            project.history.append(history)
            
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': 'Project details updated successfully'
            })
            
        elif form_type == 'roles':
            # Update project roles
            project.lead_id = request.form.get('lead_id', type=int)
            
            # Update team members
            team_members = request.form.getlist('team_members[]')
            project.team_members = User.query.filter(User.id.in_(team_members)).all()
            
            # Update watchers
            watchers = request.form.getlist('watchers[]')
            project.watchers = User.query.filter(User.id.in_(watchers)).all()
            
            # Update stakeholders
            stakeholders = request.form.getlist('stakeholders[]')
            project.stakeholders = User.query.filter(User.id.in_(stakeholders)).all()
            
            # Update shareholders
            shareholders = request.form.getlist('shareholders[]')
            project.shareholders = User.query.filter(User.id.in_(shareholders)).all()
            
            # Create history entry
            history = History(
                entity_type='project',
                action='updated',
                user_id=current_user.id,
                project_id=project.id,
                details={
                    'fields': ['roles'],
                    'lead': project.lead.name if project.lead else None,
                    'team_size': len(project.team_members)
                }
            )
            project.history.append(history)
            
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': 'Project roles updated successfully'
            })
            
        elif form_type == 'notifications':
            # Update notification settings
            project.notify_task_created = request.form.get('notify_task_created') == 'true'
            project.notify_task_completed = request.form.get('notify_task_completed') == 'true'
            project.notify_comments = request.form.get('notify_comments') == 'true'
            
            # Create history entry
            history = History(
                entity_type='project',
                action='updated',
                user_id=current_user.id,
                project_id=project.id,
                details={
                    'fields': ['notification_settings']
                }
            )
            project.history.append(history)
            
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': 'Notification settings updated successfully'
            })
            
        return jsonify({
            'status': 'error',
            'message': 'Invalid form type'
        }), 400

    return render_template('projects/settings.html',
                         project=project,
                         users=users)

# Task Routes
@bp.route('/<int:project_id>/tasks/create', methods=['POST'])
@login_required
@requires_roles('user')
@track_activity
def create_task(project_id):
    """Create a new task"""
    project = Project.query.get_or_404(project_id)
    form = TaskForm()
    users = User.query.all()
    form.assigned_to_id.choices = [(u.id, u.name) for u in users]

    if form.validate_on_submit():
        task = Task(
            project_id=project.id,
            name=form.name.data,
            description=form.description.data,
            status=form.status.data,
            priority=form.priority.data,
            assigned_to_id=form.assigned_to_id.data,
            due_date=form.due_date.data
        )

        # Create history entry
        history = History(
            entity_type='task',
            action='created',
            user_id=current_user.id,
            project_id=project.id,
            details={
                'name': task.name,
                'status': task.status,
                'priority': task.priority
            }
        )
        task.history.append(history)

        # Log activity
        activity = UserActivity(
            user_id=current_user.id,
            username=current_user.username,
            activity=f"Created new task: {task.name} in project: {project.name}"
        )

        db.session.add(task)
        db.session.add(activity)
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Task created successfully',
            'task': {
                'id': task.id,
                'name': task.name,
                'status': task.status,
                'priority': task.priority,
                'assigned_to': task.assigned_to.name if task.assigned_to else None,
                'due_date': task.due_date.strftime('%Y-%m-%d') if task.due_date else None
            }
        })

    return jsonify({
        'status': 'error',
        'message': 'Invalid form data',
        'errors': form.errors
    }), 400

# Todo Routes
@bp.route('/<int:project_id>/todos/create', methods=['POST'])
@login_required
@requires_roles('user')
@track_activity
def create_todo(project_id):
    """Create a new todo item"""
    project = Project.query.get_or_404(project_id)
    form = TodoForm()
    users = User.query.all()
    form.assigned_to_id.choices = [(u.id, u.name) for u in users]

    if form.validate_on_submit():
        todo = Todo(
            project_id=project.id,
            description=form.description.data,
            assigned_to_id=form.assigned_to_id.data
        )

        # Log activity
        activity = UserActivity(
            user_id=current_user.id,
            username=current_user.username,
            activity=f"Created new todo in project: {project.name}"
        )

        db.session.add(todo)
        db.session.add(activity)
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Todo created successfully',
            'todo': {
                'id': todo.id,
                'description': todo.description,
                'assigned_to': todo.assigned_to.name if todo.assigned_to else None
            }
        })

    return jsonify({
        'status': 'error',
        'message': 'Invalid form data',
        'errors': form.errors
    }), 400

@bp.route('/todos/<int:todo_id>/toggle', methods=['POST'])
@login_required
@requires_roles('user')
@track_activity
def toggle_todo(todo_id):
    """Toggle todo completion status"""
    todo = Todo.query.get_or_404(todo_id)
    todo.completed = not todo.completed
    todo.completed_at = datetime.utcnow() if todo.completed else None

    # Log activity
    activity = UserActivity(
        user_id=current_user.id,
        username=current_user.username,
        activity=f"{'Completed' if todo.completed else 'Uncompleted'} todo in project: {todo.project.name}"
    )

    db.session.add(activity)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'completed': todo.completed,
        'completed_at': todo.completed_at.strftime('%Y-%m-%d %H:%M:%S') if todo.completed_at else None
    })

# Comment Routes
@bp.route('/<int:project_id>/comments/create', methods=['POST'])
@login_required
@requires_roles('user')
@track_activity
def create_comment(project_id):
    """Create a new comment"""
    project = Project.query.get_or_404(project_id)
    form = CommentForm()

    if form.validate_on_submit():
        comment = Comment(
            project_id=project.id,
            content=form.content.data,
            user_id=current_user.id
        )

        # Log activity
        activity = UserActivity(
            user_id=current_user.id,
            username=current_user.username,
            activity=f"Added comment to project: {project.name}"
        )

        db.session.add(comment)
        db.session.add(activity)
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Comment added successfully',
            'comment': {
                'id': comment.id,
                'content': comment.content,
                'user': comment.user.name,
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        })

    return jsonify({
        'status': 'error',
        'message': 'Invalid form data',
        'errors': form.errors
    }), 400

# Project Management Routes
@bp.route('/<int:project_id>/archive', methods=['POST'])
@login_required
@requires_roles('user')
@track_activity
def archive_project(project_id):
    """Archive a project"""
    project = Project.query.get_or_404(project_id)
    project.status = 'archived'
    
    # Create history entry
    history = History(
        entity_type='project',
        action='archived',
        user_id=current_user.id,
        project_id=project.id,
        details={'status': 'archived'}
    )
    project.history.append(history)

    # Log activity
    activity = UserActivity(
        user_id=current_user.id,
        username=current_user.username,
        activity=f"Archived project: {project.name}"
    )
    
    db.session.add(activity)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'Project archived successfully'
    })

@bp.route('/<int:project_id>/delete', methods=['POST'])
@login_required
@requires_roles('user')
@track_activity
def delete_project(project_id):
    """Delete a project"""
    project = Project.query.get_or_404(project_id)
    project_name = project.name

    # Log activity before deletion
    activity = UserActivity(
        user_id=current_user.id,
        username=current_user.username,
        activity=f"Deleted project: {project_name}"
    )
    
    db.session.add(activity)
    db.session.delete(project)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'Project deleted successfully'
    })
