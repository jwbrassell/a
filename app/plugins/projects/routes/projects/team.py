"""Team management routes for projects."""

from flask import jsonify, request
from flask_login import login_required, current_user
from app.utils.rbac import requires_roles
from app.utils.activity_tracking import track_activity
from app.extensions import db
from app.models import User, Role
from ...models import Project
from app.plugins.projects import bp
from ...utils import can_edit_project
from .utils import (
    create_project_history,
    log_project_activity
)

@bp.route('/<int:project_id>/team', methods=['GET'])
@login_required
@requires_roles('user')
def get_project_team(project_id):
    """Get project team members"""
    project = Project.query.get_or_404(project_id)
    
    return jsonify({
        'success': True,
        'team': {
            'lead': project.lead.to_dict() if project.lead else None,
            'watchers': [u.to_dict() for u in project.watchers],
            'stakeholders': [u.to_dict() for u in project.stakeholders],
            'shareholders': [u.to_dict() for u in project.shareholders],
            'roles': [r.to_dict() for r in project.roles]
        }
    })

@bp.route('/<int:project_id>/team/watchers', methods=['POST'])
@login_required
@requires_roles('user')
@track_activity
def update_project_watchers(project_id):
    """Update project watchers"""
    project = Project.query.get_or_404(project_id)
    
    if not can_edit_project(current_user, project):
        return jsonify({
            'success': False,
            'message': 'Unauthorized to update project watchers'
        }), 403
    
    try:
        data = request.get_json()
        watcher_ids = data.get('watcher_ids', [])
        
        # Track changes
        old_watchers = set(w.id for w in project.watchers)
        new_watchers = set(watcher_ids)
        
        if old_watchers != new_watchers:
            # Get user objects
            users = User.query.filter(User.id.in_(watcher_ids)).all()
            
            # Update watchers
            project.watchers = users
            
            # Create history entry
            create_project_history(project, 'updated', current_user.id, {
                'watchers': {
                    'old': list(old_watchers),
                    'new': list(new_watchers)
                }
            })
            
            # Log activity
            log_project_activity(
                current_user.id,
                current_user.username,
                "Updated watchers for",
                project.name
            )
            
            db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Project watchers updated successfully',
            'watchers': [u.to_dict() for u in project.watchers]
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error updating project watchers: {str(e)}'
        }), 500

@bp.route('/<int:project_id>/team/stakeholders', methods=['POST'])
@login_required
@requires_roles('user')
@track_activity
def update_project_stakeholders(project_id):
    """Update project stakeholders"""
    project = Project.query.get_or_404(project_id)
    
    if not can_edit_project(current_user, project):
        return jsonify({
            'success': False,
            'message': 'Unauthorized to update project stakeholders'
        }), 403
    
    try:
        data = request.get_json()
        stakeholder_ids = data.get('stakeholder_ids', [])
        
        # Track changes
        old_stakeholders = set(s.id for s in project.stakeholders)
        new_stakeholders = set(stakeholder_ids)
        
        if old_stakeholders != new_stakeholders:
            # Get user objects
            users = User.query.filter(User.id.in_(stakeholder_ids)).all()
            
            # Update stakeholders
            project.stakeholders = users
            
            # Create history entry
            create_project_history(project, 'updated', current_user.id, {
                'stakeholders': {
                    'old': list(old_stakeholders),
                    'new': list(new_stakeholders)
                }
            })
            
            # Log activity
            log_project_activity(
                current_user.id,
                current_user.username,
                "Updated stakeholders for",
                project.name
            )
            
            db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Project stakeholders updated successfully',
            'stakeholders': [u.to_dict() for u in project.stakeholders]
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error updating project stakeholders: {str(e)}'
        }), 500

@bp.route('/<int:project_id>/team/shareholders', methods=['POST'])
@login_required
@requires_roles('user')
@track_activity
def update_project_shareholders(project_id):
    """Update project shareholders"""
    project = Project.query.get_or_404(project_id)
    
    if not can_edit_project(current_user, project):
        return jsonify({
            'success': False,
            'message': 'Unauthorized to update project shareholders'
        }), 403
    
    try:
        data = request.get_json()
        shareholder_ids = data.get('shareholder_ids', [])
        
        # Track changes
        old_shareholders = set(s.id for s in project.shareholders)
        new_shareholders = set(shareholder_ids)
        
        if old_shareholders != new_shareholders:
            # Get user objects
            users = User.query.filter(User.id.in_(shareholder_ids)).all()
            
            # Update shareholders
            project.shareholders = users
            
            # Create history entry
            create_project_history(project, 'updated', current_user.id, {
                'shareholders': {
                    'old': list(old_shareholders),
                    'new': list(new_shareholders)
                }
            })
            
            # Log activity
            log_project_activity(
                current_user.id,
                current_user.username,
                "Updated shareholders for",
                project.name
            )
            
            db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Project shareholders updated successfully',
            'shareholders': [u.to_dict() for u in project.shareholders]
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error updating project shareholders: {str(e)}'
        }), 500

@bp.route('/<int:project_id>/team/roles', methods=['POST'])
@login_required
@requires_roles('user')
@track_activity
def update_project_roles(project_id):
    """Update project roles"""
    project = Project.query.get_or_404(project_id)
    
    if not can_edit_project(current_user, project):
        return jsonify({
            'success': False,
            'message': 'Unauthorized to update project roles'
        }), 403
    
    try:
        data = request.get_json()
        role_names = data.get('role_names', [])
        
        # Track changes
        old_roles = set(r.name for r in project.roles)
        new_roles = set(role_names)
        
        if old_roles != new_roles:
            # Get role objects
            roles = Role.query.filter(Role.name.in_(role_names)).all()
            
            # Update roles
            project.roles = roles
            
            # Create history entry
            create_project_history(project, 'updated', current_user.id, {
                'roles': {
                    'old': list(old_roles),
                    'new': list(new_roles)
                }
            })
            
            # Log activity
            log_project_activity(
                current_user.id,
                current_user.username,
                "Updated roles for",
                project.name
            )
            
            db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Project roles updated successfully',
            'roles': [r.to_dict() for r in project.roles]
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error updating project roles: {str(e)}'
        }), 500
