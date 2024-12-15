"""Management routes for the projects plugin."""

from flask import render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app.utils.enhanced_rbac import requires_permission
from app.utils.plugin_base import plugin_error_handler
from . import bp, plugin
from .models import ProjectStatus, ProjectPriority, Project, History
from app.models import Role
from app import db

logger = plugin.logger

@bp.route('/manage')
@login_required
@requires_permission('projects_manage', 'read')
@plugin_error_handler
def manage():
    """Project management dashboard."""
    try:
        statuses = ProjectStatus.query.all()
        priorities = ProjectPriority.query.all()
        roles = Role.query.all()
        
        plugin.log_action('view_management', {
            'status_count': len(statuses),
            'priority_count': len(priorities)
        })
        
        return render_template('projects/manage/index.html',
                            statuses=statuses,
                            priorities=priorities,
                            roles=roles)
                            
    except Exception as e:
        logger.error(f"Error loading management dashboard: {str(e)}")
        raise

@bp.route('/manage/status', methods=['GET', 'POST'])
@login_required
@requires_permission('projects_manage', 'write')
@plugin_error_handler
def manage_status():
    """Manage project statuses."""
    try:
        if request.method == 'POST':
            # Create new status
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
            return redirect(url_for('projects.manage_status'))
            
        # GET request - show list
        statuses = ProjectStatus.query.all()
        return render_template('projects/manage/status.html',
                            statuses=statuses)
                            
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error managing statuses: {str(e)}")
        flash('Error managing statuses', 'error')
        raise

@bp.route('/manage/status/<int:id>', methods=['PUT', 'DELETE'])
@login_required
@requires_permission('projects_manage', 'write')
@plugin_error_handler
def manage_status_item(id):
    """Update or delete a status."""
    try:
        status = ProjectStatus.query.get_or_404(id)
        
        if request.method == 'DELETE':
            # Check if status is in use
            if Project.query.filter_by(status=status.name).first():
                return jsonify({
                    'error': 'Cannot delete status that is in use'
                }), 400
                
            db.session.delete(status)
            db.session.commit()
            
            plugin.log_action('delete_status', {
                'status_name': status.name
            })
            
            return jsonify({'status': 'success'})
            
        # PUT request
        data = request.get_json()
        
        # Track changes
        changes = {}
        if 'name' in data and data['name'] != status.name:
            changes['name'] = {'old': status.name, 'new': data['name']}
            status.name = data['name']
        if 'color' in data and data['color'] != status.color:
            changes['color'] = {'old': status.color, 'new': data['color']}
            status.color = data['color']
            
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
            
        return jsonify(status.to_dict())
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error managing status {id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/manage/priority', methods=['GET', 'POST'])
@login_required
@requires_permission('projects_manage', 'write')
@plugin_error_handler
def manage_priority():
    """Manage project priorities."""
    try:
        if request.method == 'POST':
            # Create new priority
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
            return redirect(url_for('projects.manage_priority'))
            
        # GET request - show list
        priorities = ProjectPriority.query.all()
        return render_template('projects/manage/priority.html',
                            priorities=priorities)
                            
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error managing priorities: {str(e)}")
        flash('Error managing priorities', 'error')
        raise

@bp.route('/manage/priority/<int:id>', methods=['PUT', 'DELETE'])
@login_required
@requires_permission('projects_manage', 'write')
@plugin_error_handler
def manage_priority_item(id):
    """Update or delete a priority."""
    try:
        priority = ProjectPriority.query.get_or_404(id)
        
        if request.method == 'DELETE':
            # Check if priority is in use
            if Project.query.filter_by(priority=priority.name).first():
                return jsonify({
                    'error': 'Cannot delete priority that is in use'
                }), 400
                
            db.session.delete(priority)
            db.session.commit()
            
            plugin.log_action('delete_priority', {
                'priority_name': priority.name
            })
            
            return jsonify({'status': 'success'})
            
        # PUT request
        data = request.get_json()
        
        # Track changes
        changes = {}
        if 'name' in data and data['name'] != priority.name:
            changes['name'] = {'old': priority.name, 'new': data['name']}
            priority.name = data['name']
        if 'color' in data and data['color'] != priority.color:
            changes['color'] = {'old': priority.color, 'new': data['color']}
            priority.color = data['color']
            
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
            
        return jsonify(priority.to_dict())
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error managing priority {id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/manage/roles', methods=['GET', 'POST'])
@login_required
@requires_permission('projects_manage', 'write')
@plugin_error_handler
def manage_roles():
    """Manage project role assignments."""
    try:
        if request.method == 'POST':
            # Update role assignments
            project_id = request.form.get('project_id')
            role_ids = request.form.getlist('roles')
            
            project = Project.query.get_or_404(project_id)
            roles = Role.query.filter(Role.id.in_(role_ids)).all()
            
            # Track changes
            old_roles = [r.name for r in project.roles]
            new_roles = [r.name for r in roles]
            
            if set(old_roles) != set(new_roles):
                project.roles = roles
                
                # Add history entry
                history = History(
                    entity_type='project',
                    project_id=project_id,
                    action='updated',
                    details={
                        'roles': {
                            'old': old_roles,
                            'new': new_roles
                        }
                    },
                    created_by=current_user.username,
                    user_id=current_user.id
                )
                db.session.add(history)
                
                db.session.commit()
                
                plugin.log_action('update_project_roles', {
                    'project_id': project_id,
                    'role_count': len(roles)
                })
                
                flash('Roles updated successfully', 'success')
            
            return redirect(url_for('projects.manage_roles'))
            
        # GET request - show form
        projects = Project.query.all()
        roles = Role.query.all()
        
        return render_template('projects/manage/roles.html',
                            projects=projects,
                            roles=roles)
                            
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error managing roles: {str(e)}")
        flash('Error managing roles', 'error')
        raise

@bp.route('/manage/settings', methods=['GET', 'POST'])
@login_required
@requires_permission('projects_manage', 'write')
@plugin_error_handler
def manage_settings():
    """Manage global project settings."""
    try:
        if request.method == 'POST':
            # Update settings
            settings = {
                'max_task_depth': int(request.form.get('max_task_depth', 3)),
                'enable_comments': bool(request.form.get('enable_comments')),
                'enable_history': bool(request.form.get('enable_history')),
                'enable_notifications': bool(request.form.get('enable_notifications'))
            }
            
            # Store settings in app config
            current_app.config['PLUGIN_PROJECTS_CONFIG'] = settings
            
            plugin.log_action('update_settings', {
                'settings': list(settings.keys())
            })
            
            flash('Settings updated successfully', 'success')
            return redirect(url_for('projects.manage_settings'))
            
        # GET request - show form
        settings = current_app.config.get('PLUGIN_PROJECTS_CONFIG', {})
        return render_template('projects/manage/settings.html',
                            settings=settings)
                            
    except Exception as e:
        logger.error(f"Error managing settings: {str(e)}")
        flash('Error managing settings', 'error')
        raise
