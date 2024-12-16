"""Role management functionality for admin module."""

from flask import render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from app.utils.enhanced_rbac import requires_permission
from app.models import Role, User, Permission
from app import db
from app.routes.admin import admin_bp as bp
from datetime import datetime
import logging
from app.utils.activity_tracking import track_activity
from sqlalchemy import func
from itertools import groupby

logger = logging.getLogger(__name__)

@bp.route('/roles')
@login_required
@requires_permission('admin_roles_access', 'read')
@track_activity
def roles():
    """List all roles."""
    roles = Role.query.order_by(Role.name).all()
    return render_template('admin/roles.html', roles=roles)

@bp.route('/roles/new', methods=['GET', 'POST'])
@login_required
@requires_permission('admin_roles_access', 'write')
@track_activity
def new_role():
    """Create a new role."""
    if request.method == 'POST':
        try:
            role = Role(
                name=request.form['name'],
                description=request.form.get('description', ''),
                icon=request.form.get('icon', 'fa-user-shield'),
                is_system_role=bool(request.form.get('is_system_role')),
                created_by=current_user.username
            )

            # Handle permissions
            if request.form.getlist('permissions[]'):
                perm_ids = [int(pid) for pid in request.form.getlist('permissions[]')]
                permissions = Permission.query.filter(Permission.id.in_(perm_ids)).all()
                role.permissions = permissions

            db.session.add(role)
            db.session.commit()
            flash(f'Role "{role.name}" created successfully.', 'success')
            return redirect(url_for('admin.roles'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating role: {e}")
            flash('Error creating role. Please try again.', 'danger')

    # Get permissions grouped by category
    permissions = Permission.query.order_by(Permission.category, Permission.name).all()
    grouped_permissions = {}
    for category, perms in groupby(permissions, key=lambda p: p.category):
        grouped_permissions[category] = list(perms)

    return render_template('admin/role_form.html',
                         role=None,
                         permissions=grouped_permissions)

@bp.route('/roles/<int:role_id>/edit', methods=['GET', 'POST'])
@login_required
@requires_permission('admin_roles_access', 'write')
@track_activity
def edit_role(role_id):
    """Edit an existing role."""
    role = Role.query.get_or_404(role_id)
    
    if request.method == 'POST':
        try:
            role.name = request.form['name']
            role.description = request.form.get('description', '')
            role.icon = request.form.get('icon', 'fa-user-shield')
            role.is_system_role = bool(request.form.get('is_system_role'))
            role.updated_by = current_user.username
            role.updated_at = datetime.utcnow()

            # Update permissions
            if request.form.getlist('permissions[]'):
                perm_ids = [int(pid) for pid in request.form.getlist('permissions[]')]
                permissions = Permission.query.filter(Permission.id.in_(perm_ids)).all()
                role.permissions = permissions
            else:
                role.permissions = []

            db.session.commit()
            flash(f'Role "{role.name}" updated successfully.', 'success')
            return redirect(url_for('admin.roles'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating role: {e}")
            flash('Error updating role. Please try again.', 'danger')

    # Get permissions grouped by category
    permissions = Permission.query.order_by(Permission.category, Permission.name).all()
    grouped_permissions = {}
    for category, perms in groupby(permissions, key=lambda p: p.category):
        grouped_permissions[category] = list(perms)

    return render_template('admin/role_form.html',
                         role=role,
                         permissions=grouped_permissions)

@bp.route('/roles/<int:role_id>/delete')
@login_required
@requires_permission('admin_roles_access', 'delete')
@track_activity
def delete_role(role_id):
    """Delete a role."""
    role = Role.query.get_or_404(role_id)
    
    if role.is_system_role:
        flash('System roles cannot be deleted.', 'danger')
        return redirect(url_for('admin.roles'))
    
    try:
        name = role.name
        db.session.delete(role)
        db.session.commit()
        flash(f'Role "{name}" deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting role: {e}")
        flash('Error deleting role. Please try again.', 'danger')
    
    return redirect(url_for('admin.roles'))

@bp.route('/roles/<int:role_id>/members')
@login_required
@requires_permission('admin_roles_access', 'read')
@track_activity
def role_members(role_id):
    """View and manage role members."""
    role = Role.query.get_or_404(role_id)
    
    # Get users not in this role for the add members modal
    available_users = User.query.filter(~User.roles.contains(role)).all()
    
    return render_template('admin/role_members.html',
                         role=role,
                         users=role.users,
                         available_users=available_users)

@bp.route('/roles/<int:role_id>/members/add', methods=['POST'])
@login_required
@requires_permission('admin_roles_access', 'write')
@track_activity
def add_role_members(role_id):
    """Add members to a role."""
    role = Role.query.get_or_404(role_id)
    
    try:
        if request.form.getlist('users[]'):
            user_ids = [int(uid) for uid in request.form.getlist('users[]')]
            users = User.query.filter(User.id.in_(user_ids)).all()
            for user in users:
                if role not in user.roles:
                    user.roles.append(role)
        
        db.session.commit()
        flash(f'Members added to role "{role.name}" successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding role members: {e}")
        flash('Error adding members to role. Please try again.', 'danger')
    
    return redirect(url_for('admin.role_members', role_id=role_id))

@bp.route('/roles/<int:role_id>/members/<int:user_id>/remove')
@login_required
@requires_permission('admin_roles_access', 'write')
@track_activity
def remove_role_member(role_id, user_id):
    """Remove a member from a role."""
    role = Role.query.get_or_404(role_id)
    user = User.query.get_or_404(user_id)
    
    try:
        if role in user.roles:
            user.roles.remove(role)
            db.session.commit()
            flash(f'User "{user.username}" removed from role "{role.name}" successfully.', 'success')
        else:
            flash(f'User "{user.username}" is not a member of role "{role.name}".', 'warning')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error removing role member: {e}")
        flash('Error removing member from role. Please try again.', 'danger')
    
    return redirect(url_for('admin.role_members', role_id=role_id))
