"""Project management routes for the projects plugin."""

from flask import render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app.utils.enhanced_rbac import requires_permission
from app.utils.plugin_base import plugin_error_handler
from . import bp, plugin
from .models import (
    Project, Task, Comment, History, ProjectStatus,
    ProjectPriority, ValidationError
)
from app.models import User, Role
from app import db

logger = plugin.logger

@bp.route('/projects')
@login_required
@requires_permission('projects_access', 'read')
@plugin_error_handler
def list_projects():
    """List all accessible projects."""
    try:
        projects = Project.query.all()
        
        plugin.log_action('list_projects', {
            'count': len(projects)
        })
        
        return render_template('projects/list.html',
                            projects=projects)
                            
    except Exception as e:
        logger.error(f"Error listing projects: {str(e)}")
        raise

@bp.route('/projects/new', methods=['GET', 'POST'])
@login_required
@requires_permission('projects_create', 'write')
@plugin_error_handler
def create_project():
    """Create a new project."""
    try:
        if request.method == 'POST':
            # Create project
            project = Project(
                name=request.form['name'],
                summary=request.form.get('summary'),
                description=request.form.get('description'),
                status=request.form.get('status'),
                priority=request.form.get('priority'),
                icon=request.form.get('icon'),
                created_by=current_user.username,
                is_private=bool(request.form.get('is_private')),
                notify_task_created=bool(request.form.get('notify_task_created')),
                notify_task_completed=bool(request.form.get('notify_task_completed')),
                notify_comments=bool(request.form.get('notify_comments'))
            )
            
            # Set project lead
            lead_id = request.form.get('lead_id')
            if lead_id:
                project.lead_id = int(lead_id)
            
            # Add watchers
            watcher_ids = request.form.getlist('watchers')
            if watcher_ids:
                watchers = User.query.filter(User.id.in_(watcher_ids)).all()
                project.watchers.extend(watchers)
            
            # Add stakeholders
            stakeholder_ids = request.form.getlist('stakeholders')
            if stakeholder_ids:
                stakeholders = User.query.filter(User.id.in_(stakeholder_ids)).all()
                project.stakeholders.extend(stakeholders)
            
            # Add shareholders
            shareholder_ids = request.form.getlist('shareholders')
            if shareholder_ids:
                shareholders = User.query.filter(User.id.in_(shareholder_ids)).all()
                project.shareholders.extend(shareholders)
            
            # Add roles
            role_ids = request.form.getlist('roles')
            if role_ids:
                roles = Role.query.filter(Role.id.in_(role_ids)).all()
                project.roles.extend(roles)
            
            db.session.add(project)
            
            # Add history entry
            history = History(
                entity_type='project',
                project_id=project.id,
                action='created',
                details={
                    'name': project.name,
                    'status': project.status,
                    'priority': project.priority
                },
                created_by=current_user.username,
                user_id=current_user.id
            )
            db.session.add(history)
            
            db.session.commit()
            
            plugin.log_action('create_project', {
                'project_id': project.id,
                'project_name': project.name
            })
            
            flash('Project created successfully', 'success')
            return redirect(url_for('projects.view_project', id=project.id))
            
        # GET request - show form
        users = User.query.all()
        roles = Role.query.all()
        statuses = ProjectStatus.query.all()
        priorities = ProjectPriority.query.all()
        
        return render_template('projects/create.html',
                            users=users,
                            roles=roles,
                            statuses=statuses,
                            priorities=priorities)
                            
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating project: {str(e)}")
        flash('Error creating project', 'error')
        raise

@bp.route('/projects/<int:id>')
@login_required
@requires_permission('projects_access', 'read')
@plugin_error_handler
def view_project(id):
    """View project details."""
    try:
        project = Project.query.get_or_404(id)
        
        plugin.log_action('view_project', {
            'project_id': project.id,
            'project_name': project.name
        })
        
        return render_template('projects/view.html',
                            project=project)
                            
    except Exception as e:
        logger.error(f"Error viewing project {id}: {str(e)}")
        raise

@bp.route('/projects/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@requires_permission('projects_edit', 'write')
@plugin_error_handler
def edit_project(id):
    """Edit project details."""
    try:
        project = Project.query.get_or_404(id)
        
        if request.method == 'POST':
            # Track changes for history
            changes = {}
            
            # Update basic fields
            for field in ['name', 'summary', 'description', 'status', 'priority', 'icon']:
                new_value = request.form.get(field)
                old_value = getattr(project, field)
                if new_value != old_value:
                    changes[field] = {'old': old_value, 'new': new_value}
                    setattr(project, field, new_value)
            
            # Update boolean fields
            for field in ['is_private', 'notify_task_created', 'notify_task_completed', 'notify_comments']:
                new_value = bool(request.form.get(field))
                old_value = getattr(project, field)
                if new_value != old_value:
                    changes[field] = {'old': old_value, 'new': new_value}
                    setattr(project, field, new_value)
            
            # Update lead
            lead_id = request.form.get('lead_id')
            if lead_id:
                new_lead_id = int(lead_id)
                if new_lead_id != project.lead_id:
                    changes['lead'] = {
                        'old': project.lead.username if project.lead else None,
                        'new': User.query.get(new_lead_id).username
                    }
                    project.lead_id = new_lead_id
            
            # Update relationships
            for relation in ['watchers', 'stakeholders', 'shareholders', 'roles']:
                ids = request.form.getlist(f'{relation}')
                if ids:
                    ids = [int(id) for id in ids]
                    current_ids = [item.id for item in getattr(project, relation)]
                    if set(ids) != set(current_ids):
                        if relation == 'roles':
                            new_items = Role.query.filter(Role.id.in_(ids)).all()
                        else:
                            new_items = User.query.filter(User.id.in_(ids)).all()
                        changes[relation] = {
                            'old': [item.name for item in getattr(project, relation)],
                            'new': [item.name for item in new_items]
                        }
                        setattr(project, relation, new_items)
            
            if changes:
                # Add history entry
                history = History(
                    entity_type='project',
                    project_id=project.id,
                    action='updated',
                    details=changes,
                    created_by=current_user.username,
                    user_id=current_user.id
                )
                db.session.add(history)
                
                db.session.commit()
                
                plugin.log_action('update_project', {
                    'project_id': project.id,
                    'project_name': project.name,
                    'changes': list(changes.keys())
                })
                
                flash('Project updated successfully', 'success')
            
            return redirect(url_for('projects.view_project', id=project.id))
            
        # GET request - show form
        users = User.query.all()
        roles = Role.query.all()
        statuses = ProjectStatus.query.all()
        priorities = ProjectPriority.query.all()
        
        return render_template('projects/edit.html',
                            project=project,
                            users=users,
                            roles=roles,
                            statuses=statuses,
                            priorities=priorities)
                            
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error editing project {id}: {str(e)}")
        flash('Error updating project', 'error')
        raise

@bp.route('/projects/<int:id>/delete', methods=['POST'])
@login_required
@requires_permission('projects_delete', 'write')
@plugin_error_handler
def delete_project(id):
    """Delete a project."""
    try:
        project = Project.query.get_or_404(id)
        name = project.name
        
        db.session.delete(project)
        db.session.commit()
        
        plugin.log_action('delete_project', {
            'project_id': id,
            'project_name': name
        })
        
        flash('Project deleted successfully', 'success')
        return redirect(url_for('projects.list_projects'))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting project {id}: {str(e)}")
        flash('Error deleting project', 'error')
        raise

@bp.route('/projects/<int:id>/team', methods=['GET', 'POST'])
@login_required
@requires_permission('projects_edit', 'write')
@plugin_error_handler
def manage_team(id):
    """Manage project team members."""
    try:
        project = Project.query.get_or_404(id)
        
        if request.method == 'POST':
            changes = {}
            
            # Update lead
            lead_id = request.form.get('lead_id')
            if lead_id:
                new_lead_id = int(lead_id)
                if new_lead_id != project.lead_id:
                    changes['lead'] = {
                        'old': project.lead.username if project.lead else None,
                        'new': User.query.get(new_lead_id).username
                    }
                    project.lead_id = new_lead_id
            
            # Update team members
            for role in ['watchers', 'stakeholders', 'shareholders']:
                member_ids = request.form.getlist(f'{role}')
                if member_ids:
                    member_ids = [int(id) for id in member_ids]
                    current_ids = [user.id for user in getattr(project, role)]
                    if set(member_ids) != set(current_ids):
                        new_members = User.query.filter(User.id.in_(member_ids)).all()
                        changes[role] = {
                            'old': [user.username for user in getattr(project, role)],
                            'new': [user.username for user in new_members]
                        }
                        setattr(project, role, new_members)
            
            if changes:
                # Add history entry
                history = History(
                    entity_type='project',
                    project_id=project.id,
                    action='updated',
                    details={'team_changes': changes},
                    created_by=current_user.username,
                    user_id=current_user.id
                )
                db.session.add(history)
                
                db.session.commit()
                
                plugin.log_action('update_team', {
                    'project_id': project.id,
                    'project_name': project.name,
                    'changes': list(changes.keys())
                })
                
                flash('Team updated successfully', 'success')
            
            return redirect(url_for('projects.view_project', id=project.id))
            
        # GET request - show form
        users = User.query.all()
        
        return render_template('projects/team.html',
                            project=project,
                            users=users)
                            
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error managing team for project {id}: {str(e)}")
        flash('Error updating team', 'error')
        raise
