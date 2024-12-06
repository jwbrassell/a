"""Main routes for the projects plugin."""

from flask import render_template, jsonify, redirect, url_for
from flask_login import login_required, current_user
from app.utils.rbac import requires_roles
from sqlalchemy import func
from app import db
from app.models import User
from ..models import Project, ProjectStatus, ProjectPriority, Task
from app.plugins.projects import bp

@bp.route('/')
@login_required
@requires_roles('user')
def index():
    """Projects dashboard view"""
    # Get all statuses and priorities
    statuses = ProjectStatus.query.all()
    priorities = ProjectPriority.query.all()
    
    # Calculate status distribution
    status_counts = {}
    for status in statuses:
        count = Project.query.filter_by(status=status.name).count()
        status_counts[status.name] = count
    
    status_labels = list(status_counts.keys())
    status_data = list(status_counts.values())
    
    # Calculate priority distribution
    priority_counts = {}
    for priority in priorities:
        count = Project.query.filter_by(priority=priority.name).count()
        priority_counts[priority.name] = count
    
    priority_labels = list(priority_counts.keys())
    priority_data = list(priority_counts.values())
    
    # Calculate team assignments
    team_assignments = db.session.query(
        Task.assigned_to_id,
        func.count(Task.id).label('task_count')
    ).group_by(Task.assigned_to_id).all()
    
    team_data = []
    team_labels = []
    for user_id, task_count in team_assignments:
        if user_id:  # Only include if there's an assigned user
            user = User.query.get(user_id)
            if user:
                team_labels.append(user.username)
                team_data.append(task_count)
    
    return render_template(
        'projects/dashboard.html',
        statuses=statuses,
        priorities=priorities,
        status_labels=status_labels,
        status_data=status_data,
        priority_labels=priority_labels,
        priority_data=priority_data,
        team_labels=team_labels,
        team_data=team_data
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
