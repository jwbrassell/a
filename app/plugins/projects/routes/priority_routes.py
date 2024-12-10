"""Priority management routes for the projects plugin."""

from flask import jsonify, request
from flask_login import login_required, current_user
from app.utils.rbac import requires_roles
from app.utils.activity_tracking import track_activity
from app.extensions import db
from app.models import UserActivity
from ..models import ProjectPriority, Project, History
from app.plugins.projects import bp

@bp.route('/priority/get', methods=['GET'])
@login_required
@requires_roles('user')
def get_priority():
    """Get a specific project priority by name"""
    name = request.args.get('name')
    if not name:
        return jsonify({
            'status': 'error',
            'message': 'Name parameter is required'
        }), 400
    
    priority = ProjectPriority.query.filter_by(name=name).first_or_404()
    return jsonify(priority.to_dict())

@bp.route('/priority/save', methods=['POST'])
@login_required
@requires_roles('admin')
@track_activity
def save_priority():
    """Create or update a project priority"""
    data = request.form
    name = data.get('name')
    color = data.get('color')
    
    if not name or not color:
        return jsonify({
            'status': 'error',
            'message': 'Name and color are required'
        }), 400
    
    priority = ProjectPriority.query.filter_by(name=name).first()
    if priority:
        # Update existing priority
        priority.color = color
        action = "Updated"
    else:
        # Create new priority
        priority = ProjectPriority(name=name, color=color)
        db.session.add(priority)
        action = "Created"
    
    # Log activity
    activity = UserActivity(
        user_id=current_user.id,
        username=current_user.username,
        activity=f"{action} project priority: {name}"
    )
    
    db.session.add(activity)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': f'Project priority {action.lower()} successfully'
    })

@bp.route('/priority/delete', methods=['POST'])
@login_required
@requires_roles('admin')
@track_activity
def delete_priority():
    """Delete a project priority by name"""
    name = request.form.get('name')
    if not name:
        return jsonify({
            'status': 'error',
            'message': 'Name parameter is required'
        }), 400
    
    priority = ProjectPriority.query.filter_by(name=name).first_or_404()
    
    # Check if priority is being used by any projects
    if Project.query.filter_by(priority=priority.name).first():
        return jsonify({
            'status': 'error',
            'message': 'Cannot delete priority as it is being used by one or more projects'
        }), 400
    
    # Log activity
    activity = UserActivity(
        user_id=current_user.id,
        username=current_user.username,
        activity=f"Deleted project priority: {name}"
    )
    
    db.session.add(activity)
    db.session.delete(priority)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'Project priority deleted successfully'
    })

@bp.route('/<int:project_id>/priority', methods=['PUT'])
@login_required
@requires_roles('user')
@track_activity
def update_project_priority(project_id):
    """Update a project's priority"""
    project = Project.query.get_or_404(project_id)
    data = request.get_json()
    
    if 'priority' not in data:
        return jsonify({
            'status': 'error',
            'message': 'Priority is required'
        }), 400
    
    old_priority = project.priority
    new_priority = data['priority']
    
    # Verify the new priority exists
    if not ProjectPriority.query.filter_by(name=new_priority).first():
        return jsonify({
            'status': 'error',
            'message': f'Priority {new_priority} does not exist'
        }), 400
    
    project.priority = new_priority
    
    # Create history entry
    history = History(
        entity_type='project',
        action='priority_updated',
        user_id=current_user.id,
        project_id=project.id,
        details={
            'old_priority': old_priority,
            'new_priority': new_priority
        }
    )
    project.history.append(history)
    
    # Log activity
    activity = UserActivity(
        user_id=current_user.id,
        username=current_user.username,
        activity=f"Updated project priority: {project.name} ({old_priority} -> {new_priority})"
    )
    
    db.session.add(activity)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'Project priority updated successfully',
        'project': project.to_dict()
    })
