"""Project CRUD routes for the projects plugin."""

from flask import jsonify, request, render_template
from flask_login import login_required, current_user
from app.utils.rbac import requires_roles
from app.utils.activity_tracking import track_activity
from app.extensions import db
from app.models import UserActivity
from ..models import Project, History, ProjectStatus, ProjectPriority
from app.plugins.projects import bp

@bp.route('/list')
@login_required
@requires_roles('user')
def list_projects():
    """List all projects grouped by status"""
    statuses = ProjectStatus.query.all()
    projects = Project.query.all()
    
    # Group projects by status
    projects_by_status = {}
    for status in statuses:
        projects_by_status[status.name] = [
            p for p in projects if p.status == status.name
        ]
    
    return render_template(
        'projects/list.html',
        statuses=statuses,
        projects_by_status=projects_by_status
    )

@bp.route('/new', methods=['GET'])
@login_required
@requires_roles('user')
def new_project():
    """Render the create project form"""
    statuses = ProjectStatus.query.all()
    priorities = ProjectPriority.query.all()
    return render_template(
        'projects/create.html',
        statuses=statuses,
        priorities=priorities
    )

@bp.route('/create', methods=['POST'])
@login_required
@requires_roles('user')
@track_activity
def create_project():
    """Create a new project"""
    data = request.get_json()
    
    project = Project(
        name=data['name'],
        description=data.get('description', ''),
        status=data.get('status', 'new'),
        priority=data.get('priority', 'medium'),
        percent_complete=data.get('percent_complete', 0),
        lead_id=current_user.id
    )
    
    # Create history entry
    history = History(
        entity_type='project',
        action='created',
        user_id=current_user.id,
        details=data
    )
    project.history.append(history)
    
    # Log activity
    activity = UserActivity(
        user_id=current_user.id,
        username=current_user.username,
        activity=f"Created project: {project.name}"
    )
    
    db.session.add(project)
    db.session.add(activity)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'Project created successfully',
        'project': project.to_dict()
    })

@bp.route('/<int:project_id>', methods=['GET'])
@login_required
@requires_roles('user')
def get_project(project_id):
    """Get a specific project"""
    project = Project.query.get_or_404(project_id)
    return jsonify(project.to_dict())

@bp.route('/<int:project_id>', methods=['PUT'])
@login_required
@requires_roles('user')
@track_activity
def update_project(project_id):
    """Update a project"""
    project = Project.query.get_or_404(project_id)
    data = request.get_json()
    
    # Track changes for history
    changes = {}
    for key, value in data.items():
        if hasattr(project, key) and getattr(project, key) != value:
            changes[key] = {'old': getattr(project, key), 'new': value}
            setattr(project, key, value)
    
    if changes:
        # Create history entry
        history = History(
            entity_type='project',
            action='updated',
            user_id=current_user.id,
            project_id=project.id,
            details=changes
        )
        project.history.append(history)
        
        # Log activity
        activity = UserActivity(
            user_id=current_user.id,
            username=current_user.username,
            activity=f"Updated project: {project.name}"
        )
        db.session.add(activity)
    
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'Project updated successfully',
        'project': project.to_dict()
    })

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
