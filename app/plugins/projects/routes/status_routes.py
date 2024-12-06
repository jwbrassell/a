"""Status management routes for the projects plugin."""

from flask import jsonify, request
from flask_login import login_required, current_user
from app.utils.rbac import requires_roles
from app.utils.activity_tracking import track_activity
from app.extensions import db
from app.models import UserActivity
from ..models import ProjectStatus, Project, History
from app.plugins.projects import bp

@bp.route('/status/get', methods=['GET'])
@login_required
@requires_roles('user')
def get_status():
    """Get a specific project status by name"""
    name = request.args.get('name')
    if not name:
        return jsonify({
            'status': 'error',
            'message': 'Name parameter is required'
        }), 400
    
    status = ProjectStatus.query.filter_by(name=name).first_or_404()
    return jsonify(status.to_dict())

@bp.route('/status/save', methods=['POST'])
@login_required
@requires_roles('admin')
@track_activity
def save_status():
    """Create or update a project status"""
    data = request.form
    name = data.get('name')
    color = data.get('color')
    
    if not name or not color:
        return jsonify({
            'status': 'error',
            'message': 'Name and color are required'
        }), 400
    
    status = ProjectStatus.query.filter_by(name=name).first()
    if status:
        # Update existing status
        status.color = color
        action = "Updated"
    else:
        # Create new status
        status = ProjectStatus(name=name, color=color)
        db.session.add(status)
        action = "Created"
    
    # Log activity
    activity = UserActivity(
        user_id=current_user.id,
        username=current_user.username,
        activity=f"{action} project status: {name}"
    )
    
    db.session.add(activity)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': f'Project status {action.lower()} successfully'
    })

@bp.route('/status/delete', methods=['POST'])
@login_required
@requires_roles('admin')
@track_activity
def delete_status():
    """Delete a project status by name"""
    name = request.form.get('name')
    if not name:
        return jsonify({
            'status': 'error',
            'message': 'Name parameter is required'
        }), 400
    
    status = ProjectStatus.query.filter_by(name=name).first_or_404()
    
    # Check if status is being used by any projects
    if Project.query.filter_by(status=status.name).first():
        return jsonify({
            'status': 'error',
            'message': 'Cannot delete status as it is being used by one or more projects'
        }), 400
    
    # Log activity
    activity = UserActivity(
        user_id=current_user.id,
        username=current_user.username,
        activity=f"Deleted project status: {name}"
    )
    
    db.session.add(activity)
    db.session.delete(status)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'Project status deleted successfully'
    })

@bp.route('/<int:project_id>/status', methods=['PUT'])
@login_required
@requires_roles('user')
@track_activity
def update_project_status(project_id):
    """Update a project's status"""
    project = Project.query.get_or_404(project_id)
    data = request.get_json()
    
    if 'status' not in data:
        return jsonify({
            'status': 'error',
            'message': 'Status is required'
        }), 400
    
    old_status = project.status
    new_status = data['status']
    
    # Verify the new status exists
    if not ProjectStatus.query.filter_by(name=new_status).first():
        return jsonify({
            'status': 'error',
            'message': f'Status {new_status} does not exist'
        }), 400
    
    project.status = new_status
    
    # Create history entry
    history = History(
        entity_type='project',
        action='status_updated',
        user_id=current_user.id,
        project_id=project.id,
        details={
            'old_status': old_status,
            'new_status': new_status
        }
    )
    project.history.append(history)
    
    # Log activity
    activity = UserActivity(
        user_id=current_user.id,
        username=current_user.username,
        activity=f"Updated project status: {project.name} ({old_status} -> {new_status})"
    )
    
    db.session.add(activity)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'Project status updated successfully',
        'project': project.to_dict()
    })
