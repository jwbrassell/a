"""Routes for project management."""

from flask import render_template, jsonify, redirect, url_for, current_app, request
from flask_login import login_required, current_user
from app.utils.rbac import requires_roles
from app.utils.activity_tracking import track_activity
from app.extensions import db
from app.models import User, UserActivity
from .models import Project, ProjectStatus, ProjectPriority, Task, History
from . import bp
from .utils.project_utils import (
    can_edit_project,
    can_view_project,
    get_project_stats
)
from datetime import date, datetime

# Main routes
@bp.route('/')
@login_required
@requires_roles('user')
def index():
    """Projects index view"""
    try:
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
    except Exception as e:
        current_app.logger.error(f"Error in projects index: {str(e)}")
        return render_template('projects/error.html', error="Error loading projects dashboard"), 500

@bp.route('/dashboard')
@login_required
@requires_roles('user')
def project_dashboard():
    """Project dashboard view"""
    try:
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
    except Exception as e:
        current_app.logger.error(f"Error loading project dashboard: {str(e)}")
        return render_template('projects/error.html', error="Error loading dashboard"), 500

# Project routes
@bp.route('/create', methods=['GET', 'POST'])
@login_required
@requires_roles('user')
def create_project():
    """Create new project"""
    try:
        if request.method == 'POST':
            data = request.get_json() or request.form.to_dict()
            
            project = Project(
                name=data['name'],
                summary=data.get('summary'),
                description=data.get('description'),
                status=data.get('status', 'Not Started'),
                priority=data.get('priority', 'Medium'),
                created_by=current_user.username,
                lead_id=data.get('lead_id')
            )
            
            db.session.add(project)
            
            # Create history entry
            history = History(
                entity_type='project',
                action='created',
                user_id=current_user.id,
                project_id=project.id,
                details={
                    'name': project.name,
                    'status': project.status,
                    'priority': project.priority
                }
            )
            project.history.append(history)
            
            # Log activity
            activity = UserActivity(
                user_id=current_user.id,
                username=current_user.username,
                activity=f"Created new project: {project.name}"
            )
            db.session.add(activity)
            
            db.session.commit()
            
            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': 'Project created successfully',
                    'project': project.to_dict()
                })
            
            return redirect(url_for('projects.view_project', project_id=project.id))
            
        # GET request - show create form
        users = User.query.all()
        statuses = ProjectStatus.query.all()
        priorities = ProjectPriority.query.all()
        
        return render_template(
            'projects/create.html',
            users=users,
            statuses=statuses,
            priorities=priorities
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating project: {str(e)}")
        if request.is_json:
            return jsonify({
                'success': False,
                'message': 'Error creating project'
            }), 500
        return render_template('projects/error.html', error="Error creating project"), 500

@bp.route('/<int:project_id>/view')
@login_required
@requires_roles('user')
def view_project(project_id):
    """View project details"""
    try:
        project = Project.query.get_or_404(project_id)
        if not can_view_project(current_user, project):
            current_app.logger.warning(
                f"User {current_user.username} attempted to view unauthorized project {project_id}"
            )
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
    except Exception as e:
        current_app.logger.error(f"Error viewing project {project_id}: {str(e)}")
        return render_template('projects/error.html', error="Error loading project"), 500

# API routes
@bp.route('/api/projects/stats')
@login_required
@requires_roles('user')
def get_project_statistics():
    """Get project statistics for charts"""
    try:
        all_projects = Project.query.all()
        visible_projects = [p for p in all_projects if can_view_project(current_user, p)]
        
        stats = {
            'status_distribution': {},
            'priority_distribution': {},
            'team_workload': {},
            'completion_rate': {
                'completed': len([p for p in visible_projects if p.status == 'completed']),
                'in_progress': len([p for p in visible_projects if p.status == 'active']),
                'not_started': len([p for p in visible_projects if p.status == 'planning'])
            }
        }
        
        # Calculate distributions
        for project in visible_projects:
            # Status distribution
            stats['status_distribution'][project.status] = \
                stats['status_distribution'].get(project.status, 0) + 1
                
            # Priority distribution
            stats['priority_distribution'][project.priority] = \
                stats['priority_distribution'].get(project.priority, 0) + 1
                
            # Team workload
            if project.lead:
                stats['team_workload'][project.lead.username] = \
                    stats['team_workload'].get(project.lead.username, 0) + 1
        
        return jsonify(stats)
    except Exception as e:
        current_app.logger.error(f"Error getting project statistics: {str(e)}")
        return jsonify({'error': 'Error retrieving project statistics'}), 500

# Error handlers
@bp.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors."""
    return {
        'success': False,
        'message': 'Resource not found'
    }, 404

@bp.errorhandler(403)
def forbidden_error(error):
    """Handle 403 errors."""
    return {
        'success': False,
        'message': 'You do not have permission to perform this action'
    }, 403

@bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return {
        'success': False,
        'message': 'An internal error occurred'
    }, 500
