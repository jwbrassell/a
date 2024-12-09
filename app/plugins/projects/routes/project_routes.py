"""Project view routes for the projects plugin."""

from flask import render_template, jsonify, redirect, url_for
from flask_login import login_required, current_user
from app.utils.rbac import requires_roles
from app.models import User
from ..models import Project, ProjectStatus, ProjectPriority, Task
from app.plugins.projects import bp
from .projects.utils import (
    can_edit_project,
    can_view_project,
    get_project_stats
)

@bp.route('/<int:project_id>/view')
@login_required
@requires_roles('user')
def view_project(project_id):
    """View project details"""
    project = Project.query.get_or_404(project_id)
    if not can_view_project(current_user, project):
        return redirect(url_for('projects.project_dashboard'))
    
    # Get all users, statuses, and priorities for dropdowns
    users = User.query.all()
    statuses = ProjectStatus.query.all()
    priorities = ProjectPriority.query.all()
    
    return render_template(
        'projects/view.html',
        project=project,
        users=users,
        statuses=statuses,
        priorities=priorities,
        readonly=True,
        can_edit=can_edit_project(current_user, project)
    )

@bp.route('/dashboard')
@login_required
@requires_roles('user')
def project_dashboard():
    """Project dashboard view"""
    # Get all statuses and priorities
    statuses = ProjectStatus.query.all()
    priorities = ProjectPriority.query.all()
    
    # Get projects user can view
    all_projects = Project.query.all()
    visible_projects = [p for p in all_projects if can_view_project(current_user, p)]
    
    # Calculate status distribution
    status_counts = {}
    for status in statuses:
        count = len([p for p in visible_projects if p.status == status.name])
        status_counts[status.name] = count
    
    status_labels = list(status_counts.keys()) if status_counts else []
    status_data = list(status_counts.values()) if status_counts else []
    
    # Calculate priority distribution
    priority_counts = {}
    for priority in priorities:
        count = len([p for p in visible_projects if p.priority == priority.name])
        priority_counts[priority.name] = count
    
    priority_labels = list(priority_counts.keys()) if priority_counts else []
    priority_data = list(priority_counts.values()) if priority_counts else []
    
    # Calculate team assignments
    team_assignments = {}
    for project in visible_projects:
        for task in project.tasks:
            if task.assigned_to:
                username = task.assigned_to.username
                team_assignments[username] = team_assignments.get(username, 0) + 1
    
    team_labels = list(team_assignments.keys()) if team_assignments else []
    team_data = list(team_assignments.values()) if team_assignments else []
    
    # Get statistics
    total_projects = len(visible_projects)
    active_projects = len([p for p in visible_projects if p.status == 'active'])
    completed_projects = len([p for p in visible_projects if p.status == 'completed'])
    
    # Get recent activity
    recent_projects = sorted(
        visible_projects,
        key=lambda p: p.updated_at or p.created_at,
        reverse=True
    )[:5]
    
    return render_template(
        'projects/dashboard.html',
        total_projects=total_projects,
        active_projects=active_projects,
        completed_projects=completed_projects,
        recent_projects=recent_projects,
        statuses=statuses,
        priorities=priorities,
        status_labels=status_labels or [],
        status_data=status_data or [],
        priority_labels=priority_labels or [],
        priority_data=priority_data or [],
        team_labels=team_labels or [],
        team_data=team_data or []
    )

@bp.route('/kanban')
@login_required
@requires_roles('user')
def project_kanban():
    """Kanban board view for projects"""
    # Get projects user can view
    all_projects = Project.query.all()
    visible_projects = [p for p in all_projects if can_view_project(current_user, p)]
    
    # Group projects by status
    projects_by_status = {
        'planning': [],
        'active': [],
        'on_hold': [],
        'completed': [],
        'archived': []
    }
    
    for project in visible_projects:
        status = project.status or 'planning'
        if status in projects_by_status:
            projects_by_status[status].append(project)
    
    return render_template(
        'projects/kanban.html',
        projects_by_status=projects_by_status
    )

@bp.route('/calendar')
@login_required
@requires_roles('user')
def project_calendar():
    """Calendar view for projects"""
    # Get projects user can view
    all_projects = Project.query.all()
    visible_projects = [p for p in all_projects if can_view_project(current_user, p)]
    
    # Get all tasks with due dates
    calendar_items = []
    for project in visible_projects:
        # Add project tasks
        for task in project.tasks:
            if task.due_date:
                calendar_items.append({
                    'title': task.name,
                    'date': task.due_date.isoformat(),
                    'type': 'task',
                    'project': project.name,
                    'url': f'/projects/task/{task.id}/view'
                })
        
        # Add project todos
        for todo in project.todos:
            if todo.due_date:
                calendar_items.append({
                    'title': todo.description,
                    'date': todo.due_date.isoformat(),
                    'type': 'todo',
                    'project': project.name,
                    'url': f'/projects/{project.id}/view#todo-{todo.id}'
                })
    
    return render_template(
        'projects/calendar.html',
        calendar_items=calendar_items
    )

@bp.route('/timeline')
@login_required
@requires_roles('user')
def project_timeline():
    """Timeline view for projects"""
    # Get projects user can view
    all_projects = Project.query.all()
    visible_projects = [p for p in all_projects if can_view_project(current_user, p)]
    
    # Get all history entries
    timeline_items = []
    for project in visible_projects:
        for history in project.history:
            timeline_items.append({
                'date': history.created_at,
                'user': history.user.username if history.user else 'System',
                'action': history.action,
                'details': history.details,
                'project': project.name,
                'type': history.entity_type,
                'icon': history.icon,
                'color': history.color
            })
    
    # Sort by date descending
    timeline_items.sort(key=lambda x: x['date'], reverse=True)
    
    return render_template(
        'projects/timeline.html',
        timeline_items=timeline_items
    )

@bp.route('/settings')
@login_required
@requires_roles('admin')
def project_settings():
    """Project settings view"""
    statuses = ProjectStatus.query.all()
    priorities = ProjectPriority.query.all()
    users = User.query.all()
    
    return render_template(
        'projects/settings.html',
        statuses=statuses,
        priorities=priorities,
        users=users
    )

@bp.route('/reports')
@login_required
@requires_roles('user')
def project_reports():
    """Project reports view"""
    # Get projects user can view
    all_projects = Project.query.all()
    visible_projects = [p for p in all_projects if can_view_project(current_user, p)]
    
    # Calculate statistics for each project
    project_stats = {
        project.id: get_project_stats(project)
        for project in visible_projects
    }
    
    return render_template(
        'projects/reports.html',
        projects=visible_projects,
        project_stats=project_stats
    )
