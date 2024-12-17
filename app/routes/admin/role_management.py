"""Role management functionality for admin module."""

from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from app.utils.enhanced_rbac import requires_permission, has_permission
from app.models import Role, User, Permission, UserActivity
from app import db
from app.routes.admin import admin_bp as bp
from datetime import datetime, timedelta
import logging
from app.utils.activity_tracking import track_activity
from sqlalchemy import func, desc

logger = logging.getLogger(__name__)

class RoleForm(FlaskForm):
    """Empty form class for CSRF protection."""
    pass

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
    form = RoleForm()
    if request.method == 'POST' and form.validate_on_submit():
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
            
            # Track activity
            activity = UserActivity(
                user_id=current_user.id,
                username=current_user.username,
                action='create_role',
                resource=f'role_{role.name}',
                details=f'Created new role: {role.name}',
                activity=f'Created role {role.name}'  # Backward compatibility
            )
            db.session.add(activity)
            
            db.session.commit()
            flash(f'Role "{role.name}" created successfully.', 'success')
            return redirect(url_for('admin.roles'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating role: {e}")
            flash('Error creating role. Please try again.', 'danger')

    # Get permissions grouped by category
    permissions = Permission.get_grouped_permissions()

    return render_template('admin/role_form.html',
                         role=None,
                         permissions=permissions,
                         form=form)

@bp.route('/roles/<int:role_id>/edit', methods=['GET', 'POST'])
@login_required
@requires_permission('admin_roles_access', 'write')
@track_activity
def edit_role(role_id):
    """Edit an existing role."""
    role = Role.query.get_or_404(role_id)
    form = RoleForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        try:
            old_permissions = set(role.permissions)
            
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
            
            # Track permission changes
            new_permissions = set(role.permissions)
            added_perms = new_permissions - old_permissions
            removed_perms = old_permissions - new_permissions
            
            changes = []
            if added_perms:
                changes.append(f"Added permissions: {', '.join(p.name for p in added_perms)}")
            if removed_perms:
                changes.append(f"Removed permissions: {', '.join(p.name for p in removed_perms)}")
            
            # Track activity with detailed changes
            activity = UserActivity(
                user_id=current_user.id,
                username=current_user.username,
                action='update_role',
                resource=f'role_{role.name}',
                details=f"Updated role {role.name}. " + " ".join(changes) if changes else f"Updated role {role.name}",
                activity=f'Updated role {role.name}'  # Backward compatibility
            )
            db.session.add(activity)

            db.session.commit()
            flash(f'Role "{role.name}" updated successfully.', 'success')
            return redirect(url_for('admin.roles'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating role: {e}")
            flash('Error updating role. Please try again.', 'danger')

    # Get permissions grouped by category
    permissions = Permission.get_grouped_permissions()

    return render_template('admin/role_form.html',
                         role=role,
                         permissions=permissions,
                         form=form)

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
        
        # Track activity before deletion
        activity = UserActivity(
            user_id=current_user.id,
            username=current_user.username,
            action='delete_role',
            resource=f'role_{name}',
            details=f'Deleted role: {name}',
            activity=f'Deleted role {name}'  # Backward compatibility
        )
        db.session.add(activity)
        
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
    form = RoleForm()
    
    # Get users not in this role for the add members modal, sorted by username
    available_users = User.query.filter(
        ~User.roles.contains(role),
        User.is_active == True  # Only show active users
    ).order_by(User.username).all()
    
    # Get role members sorted by username
    role_users = User.query.join(User.roles).filter(
        Role.id == role_id
    ).order_by(User.username).all()
    
    # Get recent activities for this role with proper filtering
    activities = UserActivity.query.filter(
        (UserActivity.resource == f'role_{role.name}') |
        (UserActivity.activity.like(f'%role {role.name}%')),  # For backward compatibility
        UserActivity.timestamp >= datetime.utcnow() - timedelta(days=7)
    ).order_by(desc(UserActivity.timestamp)).all()
    
    # Check if current user can modify system roles
    can_modify_system = has_permission('admin_system_roles_access')
    
    return render_template('admin/role_members.html',
                         role=role,
                         users=role_users,
                         available_users=available_users,
                         activities=activities,
                         can_modify_system=can_modify_system,
                         form=form)

@bp.route('/roles/<int:role_id>/members/add', methods=['POST'])
@login_required
@requires_permission('admin_roles_access', 'write')
@track_activity
def add_role_members(role_id):
    """Add members to a role."""
    role = Role.query.get_or_404(role_id)
    form = RoleForm()
    
    if role.is_system_role and not has_permission('admin_system_roles_access'):
        return jsonify({
            'success': False,
            'message': 'You do not have permission to modify system roles.'
        }), 403
    
    if form.validate_on_submit():
        try:
            user_ids = request.form.getlist('users[]')
            if not user_ids:
                return jsonify({
                    'success': False,
                    'message': 'Please select at least one user to add.'
                }), 400

            # Get active users only
            users = User.query.filter(
                User.id.in_([int(uid) for uid in user_ids]),
                User.is_active == True
            ).all()

            if not users:
                return jsonify({
                    'success': False,
                    'message': 'No valid active users selected.'
                }), 400

            added_count = 0
            added_users = []
            for user in users:
                if role not in user.roles:
                    # Check if user is in LDAP group
                    if role.ldap_groups and any(group in role.ldap_groups for group in user.ldap_groups):
                        continue  # Skip LDAP users
                        
                    user.roles.append(role)
                    added_count += 1
                    added_users.append(f"{user.username} ({user.email})")
                    
            if added_count == 0:
                return jsonify({
                    'success': False,
                    'message': 'Selected users are either already members or managed by LDAP.'
                }), 400
            
            # Track activity with detailed user information
            activity = UserActivity(
                user_id=current_user.id,
                username=current_user.username,
                action='add_role_members',
                resource=f'role_{role.name}',
                details=f'Added users to role {role.name}: {", ".join(added_users)}',
                activity=f'Added {added_count} members to role {role.name}'  # Backward compatibility
            )
            db.session.add(activity)
            
            db.session.commit()
            return jsonify({
                'success': True,
                'message': f'{added_count} member{"s" if added_count != 1 else ""} added to role "{role.name}" successfully.'
            })
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding role members: {e}")
            return jsonify({
                'success': False,
                'message': 'Error adding members to role. Please try again.'
            }), 500
    
    return jsonify({
        'success': False,
        'message': 'Invalid form submission.'
    }), 400

@bp.route('/roles/<int:role_id>/members/<int:user_id>/remove', methods=['POST'])
@login_required
@requires_permission('admin_roles_access', 'write')
@track_activity
def remove_role_member(role_id, user_id):
    """Remove a member from a role."""
    role = Role.query.get_or_404(role_id)
    user = User.query.get_or_404(user_id)
    form = RoleForm()
    
    if role.is_system_role and not has_permission('admin_system_roles_access'):
        return jsonify({
            'success': False,
            'message': 'You do not have permission to modify system roles.'
        }), 403
    
    if user.id == current_user.id and role.name.lower() == 'admin':
        return jsonify({
            'success': False,
            'message': 'You cannot remove yourself from the Admin role.'
        }), 400
    
    # Check if user is in LDAP group
    if role.ldap_groups and any(group in role.ldap_groups for group in user.ldap_groups):
        return jsonify({
            'success': False,
            'message': 'This user is managed by LDAP and cannot be removed directly.'
        }), 400
    
    if form.validate_on_submit():
        try:
            if role in user.roles:
                user.roles.remove(role)
                
                # Track activity with user details
                activity = UserActivity(
                    user_id=current_user.id,
                    username=current_user.username,
                    action='remove_role_member',
                    resource=f'role_{role.name}',
                    details=f'Removed user {user.username} ({user.email}) from role {role.name}',
                    activity=f'Removed user {user.username} from role {role.name}'  # Backward compatibility
                )
                db.session.add(activity)
                
                db.session.commit()
                return jsonify({
                    'success': True,
                    'message': f'User "{user.username}" removed from role "{role.name}" successfully.'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': f'User "{user.username}" is not a member of role "{role.name}".'
                }), 400
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error removing role member: {e}")
            return jsonify({
                'success': False,
                'message': 'Error removing member from role. Please try again.'
            }), 500
    
    return jsonify({
        'success': False,
        'message': 'Invalid form submission.'
    }), 400
