"""Task dependency management."""

from flask import jsonify, request
from flask_login import login_required, current_user
from app.utils.rbac import requires_roles
from app.utils.activity_tracking import track_activity
from app.extensions import db
from ...models import Task, ValidationError
from app.plugins.projects import bp

@bp.route('/task/<int:task_id>/dependencies', methods=['GET'])
@login_required
@requires_roles('user')
def get_task_dependencies(task_id):
    """Get dependencies for a task"""
    task = Task.query.get_or_404(task_id)
    return jsonify({
        'success': True,
        'dependencies': [{'id': t.id, 'name': t.name} for t in task.dependencies],
        'dependent_tasks': [{'id': t.id, 'name': t.name} for t in task.dependent_tasks]
    })

@bp.route('/task/<int:task_id>/dependencies', methods=['PUT'])
@login_required
@requires_roles('user')
@track_activity
def update_task_dependencies(task_id):
    """Update task dependencies"""
    task = Task.query.get_or_404(task_id)
    data = request.get_json()
    
    if not data or 'dependencies' not in data:
        return jsonify({
            'success': False,
            'message': 'Dependencies list is required'
        }), 400
    
    try:
        # Clear existing dependencies
        task.dependencies = []
        
        # Add new dependencies
        for dep_id in data['dependencies']:
            dependency = Task.query.get_or_404(dep_id)
            task.dependencies.append(dependency)
        
        # Validate for circular dependencies
        task.validate_dependencies()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Dependencies updated successfully',
            'dependencies': [{'id': t.id, 'name': t.name} for t in task.dependencies]
        })
        
    except ValidationError as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error updating dependencies: {str(e)}'
        }), 500

@bp.route('/task/<int:task_id>/dependencies/<int:dependency_id>', methods=['DELETE'])
@login_required
@requires_roles('user')
@track_activity
def remove_task_dependency(task_id, dependency_id):
    """Remove a dependency from a task"""
    task = Task.query.get_or_404(task_id)
    dependency = Task.query.get_or_404(dependency_id)
    
    try:
        task.dependencies.remove(dependency)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Dependency removed successfully',
            'dependencies': [{'id': t.id, 'name': t.name} for t in task.dependencies]
        })
        
    except ValueError:
        return jsonify({
            'success': False,
            'message': 'Dependency not found'
        }), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error removing dependency: {str(e)}'
        }), 500

@bp.route('/task/<int:task_id>/dependencies/check', methods=['POST'])
@login_required
@requires_roles('user')
def check_dependency_validity(task_id):
    """Check if adding a dependency would create a circular reference"""
    task = Task.query.get_or_404(task_id)
    data = request.get_json()
    
    if not data or 'dependency_id' not in data:
        return jsonify({
            'success': False,
            'message': 'Dependency ID is required'
        }), 400
    
    dependency = Task.query.get_or_404(data['dependency_id'])
    
    try:
        # Temporarily add dependency
        task.dependencies.append(dependency)
        
        # Check for circular dependencies
        task.validate_dependencies()
        
        # Remove temporary dependency
        task.dependencies.remove(dependency)
        
        return jsonify({
            'success': True,
            'message': 'Dependency is valid'
        })
        
    except ValidationError as e:
        # Remove temporary dependency
        task.dependencies.remove(dependency)
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        # Remove temporary dependency if it was added
        try:
            task.dependencies.remove(dependency)
        except ValueError:
            pass
        return jsonify({
            'success': False,
            'message': f'Error checking dependency: {str(e)}'
        }), 500
