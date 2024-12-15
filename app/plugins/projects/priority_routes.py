"""Priority management routes for the projects plugin."""

from flask import render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app.utils.enhanced_rbac import requires_permission
from app.utils.plugin_base import plugin_error_handler
from . import bp, plugin
from .models import ProjectPriority, Project, Task, History
from app import db

logger = plugin.logger

@bp.route('/priorities')
@login_required
@requires_permission('projects_manage', 'read')
@plugin_error_handler
def list_priorities():
    """List all project priorities."""
    try:
        priorities = ProjectPriority.query.order_by(ProjectPriority.name).all()
        
        # Get usage statistics
        stats = {}
        for priority in priorities:
            stats[priority.id] = {
                'projects': Project.query.filter_by(priority=priority.name).count(),
                'tasks': Task.query.filter_by(priority_id=priority.id).count()
            }
        
        plugin.log_action('list_priorities', {
            'priority_count': len(priorities)
        })
        
        return render_template('projects/priorities/list.html',
                            priorities=priorities,
                            stats=stats)
                            
    except Exception as e:
        logger.error(f"Error listing priorities: {str(e)}")
        raise

@bp.route('/priorities/new', methods=['GET', 'POST'])
@login_required
@requires_permission('projects_manage', 'write')
@plugin_error_handler
def create_priority():
    """Create a new project priority."""
    try:
        if request.method == 'POST':
            # Create priority
            priority = ProjectPriority(
                name=request.form['name'],
                color=request.form['color'],
                created_by=current_user.username
            )
            db.session.add(priority)
            
            # Add history entry
            history = History(
                entity_type='priority',
                action='created',
                details={
                    'name': priority.name,
                    'color': priority.color
                },
                created_by=current_user.username,
                user_id=current_user.id
            )
            db.session.add(history)
            
            db.session.commit()
            
            plugin.log_action('create_priority', {
                'priority_name': priority.name
            })
            
            flash('Priority created successfully', 'success')
            return redirect(url_for('projects.list_priorities'))
            
        # GET request - show form
        return render_template('projects/priorities/create.html')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating priority: {str(e)}")
        flash('Error creating priority', 'error')
        raise

@bp.route('/priorities/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@requires_permission('projects_manage', 'write')
@plugin_error_handler
def edit_priority(id):
    """Edit a project priority."""
    try:
        priority = ProjectPriority.query.get_or_404(id)
        
        if request.method == 'POST':
            # Track changes
            changes = {}
            
            # Update fields
            if request.form['name'] != priority.name:
                changes['name'] = {'old': priority.name, 'new': request.form['name']}
                priority.name = request.form['name']
                
            if request.form['color'] != priority.color:
                changes['color'] = {'old': priority.color, 'new': request.form['color']}
                priority.color = request.form['color']
            
            if changes:
                # Add history entry
                history = History(
                    entity_type='priority',
                    action='updated',
                    details=changes,
                    created_by=current_user.username,
                    user_id=current_user.id
                )
                db.session.add(history)
                
                db.session.commit()
                
                plugin.log_action('update_priority', {
                    'priority_name': priority.name,
                    'changes': list(changes.keys())
                })
                
                flash('Priority updated successfully', 'success')
            
            return redirect(url_for('projects.list_priorities'))
            
        # GET request - show form
        return render_template('projects/priorities/edit.html',
                            priority=priority)
                            
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error editing priority {id}: {str(e)}")
        flash('Error updating priority', 'error')
        raise

@bp.route('/priorities/<int:id>/delete', methods=['POST'])
@login_required
@requires_permission('projects_manage', 'write')
@plugin_error_handler
def delete_priority(id):
    """Delete a project priority."""
    try:
        priority = ProjectPriority.query.get_or_404(id)
        
        # Check if priority is in use
        if Project.query.filter_by(priority=priority.name).first() or \
           Task.query.filter_by(priority_id=priority.id).first():
            flash('Cannot delete priority that is in use', 'error')
            return redirect(url_for('projects.list_priorities'))
        
        name = priority.name
        db.session.delete(priority)
        
        # Add history entry
        history = History(
            entity_type='priority',
            action='deleted',
            details={
                'name': name,
                'color': priority.color
            },
            created_by=current_user.username,
            user_id=current_user.id
        )
        db.session.add(history)
        
        db.session.commit()
        
        plugin.log_action('delete_priority', {
            'priority_name': name
        })
        
        flash('Priority deleted successfully', 'success')
        return redirect(url_for('projects.list_priorities'))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting priority {id}: {str(e)}")
        flash('Error deleting priority', 'error')
        raise

@bp.route('/priorities/reorder', methods=['POST'])
@login_required
@requires_permission('projects_manage', 'write')
@plugin_error_handler
def reorder_priorities():
    """Update priority order."""
    try:
        data = request.get_json()
        if not data or 'priorities' not in data:
            return jsonify({'error': 'Invalid request data'}), 400
            
        # Update priority positions
        for position, priority_id in enumerate(data['priorities']):
            priority = ProjectPriority.query.get(priority_id)
            if priority:
                priority.position = position
        
        db.session.commit()
        
        plugin.log_action('reorder_priorities', {
            'priority_count': len(data['priorities'])
        })
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error reordering priorities: {str(e)}")
        return jsonify({'error': str(e)}), 500
