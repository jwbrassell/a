"""Status management routes for the projects plugin."""

from flask import render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app.utils.enhanced_rbac import requires_permission
from app.utils.plugin_base import plugin_error_handler
from . import bp, plugin
from .models import ProjectStatus, Project, Task, History
from app import db

logger = plugin.logger

@bp.route('/statuses')
@login_required
@requires_permission('projects_manage', 'read')
@plugin_error_handler
def list_statuses():
    """List all project statuses."""
    try:
        statuses = ProjectStatus.query.order_by(ProjectStatus.name).all()
        
        # Get usage statistics
        stats = {}
        for status in statuses:
            stats[status.id] = {
                'projects': Project.query.filter_by(status=status.name).count(),
                'tasks': Task.query.filter_by(status_id=status.id).count()
            }
        
        plugin.log_action('list_statuses', {
            'status_count': len(statuses)
        })
        
        return render_template('projects/statuses/list.html',
                            statuses=statuses,
                            stats=stats)
                            
    except Exception as e:
        logger.error(f"Error listing statuses: {str(e)}")
        raise

@bp.route('/statuses/new', methods=['GET', 'POST'])
@login_required
@requires_permission('projects_manage', 'write')
@plugin_error_handler
def create_status():
    """Create a new project status."""
    try:
        if request.method == 'POST':
            # Create status
            status = ProjectStatus(
                name=request.form['name'],
                color=request.form['color'],
                created_by=current_user.username
            )
            db.session.add(status)
            
            # Add history entry
            history = History(
                entity_type='status',
                action='created',
                details={
                    'name': status.name,
                    'color': status.color
                },
                created_by=current_user.username,
                user_id=current_user.id
            )
            db.session.add(history)
            
            db.session.commit()
            
            plugin.log_action('create_status', {
                'status_name': status.name
            })
            
            flash('Status created successfully', 'success')
            return redirect(url_for('projects.list_statuses'))
            
        # GET request - show form
        return render_template('projects/statuses/create.html')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating status: {str(e)}")
        flash('Error creating status', 'error')
        raise

@bp.route('/statuses/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@requires_permission('projects_manage', 'write')
@plugin_error_handler
def edit_status(id):
    """Edit a project status."""
    try:
        status = ProjectStatus.query.get_or_404(id)
        
        if request.method == 'POST':
            # Track changes
            changes = {}
            
            # Update fields
            if request.form['name'] != status.name:
                changes['name'] = {'old': status.name, 'new': request.form['name']}
                status.name = request.form['name']
                
            if request.form['color'] != status.color:
                changes['color'] = {'old': status.color, 'new': request.form['color']}
                status.color = request.form['color']
            
            if changes:
                # Add history entry
                history = History(
                    entity_type='status',
                    action='updated',
                    details=changes,
                    created_by=current_user.username,
                    user_id=current_user.id
                )
                db.session.add(history)
                
                db.session.commit()
                
                plugin.log_action('update_status', {
                    'status_name': status.name,
                    'changes': list(changes.keys())
                })
                
                flash('Status updated successfully', 'success')
            
            return redirect(url_for('projects.list_statuses'))
            
        # GET request - show form
        return render_template('projects/statuses/edit.html',
                            status=status)
                            
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error editing status {id}: {str(e)}")
        flash('Error updating status', 'error')
        raise

@bp.route('/statuses/<int:id>/delete', methods=['POST'])
@login_required
@requires_permission('projects_manage', 'write')
@plugin_error_handler
def delete_status(id):
    """Delete a project status."""
    try:
        status = ProjectStatus.query.get_or_404(id)
        
        # Check if status is in use
        if Project.query.filter_by(status=status.name).first() or \
           Task.query.filter_by(status_id=status.id).first():
            flash('Cannot delete status that is in use', 'error')
            return redirect(url_for('projects.list_statuses'))
        
        name = status.name
        db.session.delete(status)
        
        # Add history entry
        history = History(
            entity_type='status',
            action='deleted',
            details={
                'name': name,
                'color': status.color
            },
            created_by=current_user.username,
            user_id=current_user.id
        )
        db.session.add(history)
        
        db.session.commit()
        
        plugin.log_action('delete_status', {
            'status_name': name
        })
        
        flash('Status deleted successfully', 'success')
        return redirect(url_for('projects.list_statuses'))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting status {id}: {str(e)}")
        flash('Error deleting status', 'error')
        raise

@bp.route('/statuses/reorder', methods=['POST'])
@login_required
@requires_permission('projects_manage', 'write')
@plugin_error_handler
def reorder_statuses():
    """Update status order."""
    try:
        data = request.get_json()
        if not data or 'statuses' not in data:
            return jsonify({'error': 'Invalid request data'}), 400
            
        # Update status positions
        for position, status_id in enumerate(data['statuses']):
            status = ProjectStatus.query.get(status_id)
            if status:
                status.position = position
        
        db.session.commit()
        
        plugin.log_action('reorder_statuses', {
            'status_count': len(data['statuses'])
        })
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error reordering statuses: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/statuses/workflow', methods=['GET', 'POST'])
@login_required
@requires_permission('projects_manage', 'write')
@plugin_error_handler
def manage_workflow():
    """Manage status workflow transitions."""
    try:
        if request.method == 'POST':
            data = request.get_json()
            if not data or 'transitions' not in data:
                return jsonify({'error': 'Invalid request data'}), 400
                
            # Update workflow transitions in config
            current_app.config['PLUGIN_PROJECTS_CONFIG']['status_workflow'] = data['transitions']
            
            plugin.log_action('update_workflow', {
                'transition_count': len(data['transitions'])
            })
            
            return jsonify({'status': 'success'})
            
        # GET request - show workflow editor
        statuses = ProjectStatus.query.order_by(ProjectStatus.name).all()
        workflow = current_app.config.get('PLUGIN_PROJECTS_CONFIG', {}).get('status_workflow', {})
        
        return render_template('projects/statuses/workflow.html',
                            statuses=statuses,
                            workflow=workflow)
                            
    except Exception as e:
        logger.error(f"Error managing workflow: {str(e)}")
        if request.method == 'POST':
            return jsonify({'error': str(e)}), 500
        flash('Error managing workflow', 'error')
        raise
