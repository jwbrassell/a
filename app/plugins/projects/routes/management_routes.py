"""Management routes for project statuses and priorities."""

from flask import jsonify, request, render_template
from flask_login import login_required, current_user
from app.utils.rbac import requires_roles
from app.extensions import db
from ..models import ProjectStatus, ProjectPriority
from app.plugins.projects import bp

# Status Management
@bp.route('/status', methods=['GET'])
@login_required
@requires_roles('admin')
def get_status():
    """Get status details"""
    name = request.args.get('name')
    status = ProjectStatus.query.filter_by(name=name).first_or_404()
    return jsonify({
        'name': status.name,
        'color': status.color
    })

@bp.route('/status/save', methods=['POST'])
@login_required
@requires_roles('admin')
def save_status():
    """Save status"""
    if request.is_json:
        data = request.get_json()
    else:
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
        status.color = color
    else:
        status = ProjectStatus(name=name, color=color)
        db.session.add(status)
    
    try:
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': 'Status saved successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/status/delete', methods=['POST'])
@login_required
@requires_roles('admin')
def delete_status():
    """Delete status"""
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form
    
    name = data.get('name')
    
    if not name:
        return jsonify({
            'status': 'error',
            'message': 'Status name is required'
        }), 400
    
    status = ProjectStatus.query.filter_by(name=name).first_or_404()
    
    try:
        db.session.delete(status)
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': 'Status deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Priority Management
@bp.route('/priority', methods=['GET'])
@login_required
@requires_roles('admin')
def get_priority():
    """Get priority details"""
    name = request.args.get('name')
    priority = ProjectPriority.query.filter_by(name=name).first_or_404()
    return jsonify({
        'name': priority.name,
        'color': priority.color
    })

@bp.route('/priority/save', methods=['POST'])
@login_required
@requires_roles('admin')
def save_priority():
    """Save priority"""
    if request.is_json:
        data = request.get_json()
    else:
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
        priority.color = color
    else:
        priority = ProjectPriority(name=name, color=color)
        db.session.add(priority)
    
    try:
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': 'Priority saved successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/priority/delete', methods=['POST'])
@login_required
@requires_roles('admin')
def delete_priority():
    """Delete priority"""
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form
    
    name = data.get('name')
    
    if not name:
        return jsonify({
            'status': 'error',
            'message': 'Priority name is required'
        }), 400
    
    priority = ProjectPriority.query.filter_by(name=name).first_or_404()
    
    try:
        db.session.delete(priority)
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': 'Priority deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
