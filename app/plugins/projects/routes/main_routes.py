"""Main routes for the projects plugin."""

from flask import render_template, jsonify
from flask_login import login_required, current_user
from app.utils.rbac import requires_roles
from sqlalchemy import func
from datetime import date
from app import db
from app.models import User
from ..models import Project, ProjectStatus, ProjectPriority, Task
from app.plugins.projects import bp

@bp.route('/')
@login_required
@requires_roles('user')
def index():
    """Projects index view"""
    # Get active projects count
    active_projects = Project.query.filter_by(status='active').count()
    
    # Get tasks due today
    tasks_due_today = Task.query.filter(
        Task.due_date == date.today(),
        Task.list_position != 'completed'
    ).count()
    
    # Get open tasks count
    open_tasks = Task.query.filter(
        Task.list_position != 'completed'
    ).count()
    
    # Get tasks assigned to current user
    my_tasks = Task.query.filter(
        Task.assigned_to_id == current_user.id,
        Task.list_position != 'completed'
    ).count()
    
    return render_template(
        'projects/index.html',
        active_projects=active_projects,
        tasks_due_today=tasks_due_today,
        open_tasks=open_tasks,
        my_tasks=my_tasks
    )

@bp.route('/data')
@login_required
@requires_roles('user')
def get_projects():
    """Get all projects"""
    projects = Project.query.all()
    return jsonify([project.to_dict() for project in projects])

@bp.route('/status/data')
@login_required
@requires_roles('user')
def get_statuses():
    """Get all project statuses"""
    statuses = ProjectStatus.query.all()
    return jsonify([status.to_dict() for status in statuses])

@bp.route('/priority/data')
@login_required
@requires_roles('user')
def get_priorities():
    """Get all project priorities"""
    priorities = ProjectPriority.query.all()
    return jsonify([priority.to_dict() for priority in priorities])
