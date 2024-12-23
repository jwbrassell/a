"""Role management routes."""
from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from app.utils.enhanced_rbac import requires_permission
from app.models import Role, Permission
from app.extensions import db
from app.routes.admin import admin_bp as bp
from datetime import datetime
import logging
from app.utils.activity_tracking import track_activity
from app.mock_ldap import MockLDAP

logger = logging.getLogger(__name__)

# Role Management
@bp.route('/roles')
@login_required
@requires_permission('admin_roles_access', 'read')
@track_activity
def roles():
    """List all roles and their permissions."""
    roles = Role.query.order_by(Role.weight.desc(), Role.name).all()
    return render_template('admin/roles.html', roles=roles)

@bp.route('/roles/new', methods=['GET', 'POST'])
@login_required
@requires_permission('admin_roles_access', 'write')
@track_activity
def new_role():
    """Create a new role."""
    if request.method == 'POST':
        try:
            # Basic role info
            role = Role(
                name=request.form['name'],
                description=request.form.get('description'),
                notes=request.form.get('notes'),
                icon=request.form.get('icon', 'fa-user-shield'),
                is_system_role=bool(request.form.get('is_system_role')),
                weight=int(request.form.get('weight', 0)),
                created_by=current_user.username,
                ldap_groups=[]  # Initialize with empty list
            )
            
            # Set parent role if specified
            if request.form.get('parent_id'):
                role.parent_id = int(request.form['parent_id'])
            
            # Add permissions
            if request.form.getlist('permissions[]'):
                permission_ids = [int(pid) for pid in request.form.getlist('permissions[]')]
                permissions = Permission.query.filter(Permission.id.in_(permission_ids)).all()
                role.permissions = permissions
            
            # Handle LDAP group mappings
            if request.form.getlist('ldap_groups[]'):
                role.ldap_groups = request.form.getlist('ldap_groups[]')
                role.auto_sync = bool(request.form.get('auto_sync'))
            
            db.session.add(role)
            db.session.commit()
            
            flash(f'Role "{role.name}" created successfully.', 'success')
            return redirect(url_for('admin.roles'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating role: {e}")
            flash('Error creating role. Please try again.', 'danger')
    
    # Get all available roles for parent selection
    available_roles = Role.query.order_by(Role.weight.desc(), Role.name).all()
    
    # Get all permissions grouped by category
    permissions = Permission.query.order_by(Permission.category, Permission.name).all()
    
    # Get LDAP groups
    ldap = MockLDAP()
    ldap_groups = ldap.get_groups()
    
    return render_template('admin/role_form.html',
                         role=None,
                         available_roles=available_roles,
                         permissions=permissions,
                         ldap_groups=ldap_groups)

@bp.route('/roles/<int:role_id>/edit', methods=['GET', 'POST'])
@login_required
@requires_permission('admin_roles_access', 'write')
@track_activity
def edit_role(role_id):
    """Edit an existing role."""
    role = Role.query.get_or_404(role_id)
    
    # Initialize ldap_groups if it's None
    if role.ldap_groups is None:
        role.ldap_groups = []
        db.session.commit()
    
    if request.method == 'POST':
        try:
            # Update basic info
            role.name = request.form['name']
            role.description = request.form.get('description')
            role.notes = request.form.get('notes')
            role.icon = request.form.get('icon', 'fa-user-shield')
            role.is_system_role = bool(request.form.get('is_system_role'))
            role.weight = int(request.form.get('weight', 0))
            role.updated_by = current_user.username
            role.updated_at = datetime.utcnow()
            
            # Update parent role
            new_parent_id = request.form.get('parent_id')
            if new_parent_id:
                role.parent_id = int(new_parent_id)
            else:
                role.parent_id = None
            
            # Update permissions
            if request.form.getlist('permissions[]'):
                permission_ids = [int(pid) for pid in request.form.getlist('permissions[]')]
                permissions = Permission.query.filter(Permission.id.in_(permission_ids)).all()
                role.permissions = permissions
            else:
                role.permissions = []
            
            # Update LDAP group mappings
            if request.form.getlist('ldap_groups[]'):
                role.ldap_groups = request.form.getlist('ldap_groups[]')
                role.auto_sync = bool(request.form.get('auto_sync'))
            else:
                role.ldap_groups = []
                role.auto_sync = False
            
            db.session.commit()
            flash(f'Role "{role.name}" updated successfully.', 'success')
            return redirect(url_for('admin.roles'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating role: {e}")
            flash('Error updating role. Please try again.', 'danger')
    
    # Get all available roles for parent selection (excluding self and descendants)
    available_roles = [r for r in Role.query.all() 
                      if r != role and not r.is_descendant_of(role)]
    
    # Get all permissions grouped by category
    permissions = Permission.query.order_by(Permission.category, Permission.name).all()
    
    # Get LDAP groups
    ldap = MockLDAP()
    ldap_groups = ldap.get_groups()
    
    return render_template('admin/role_form.html',
                         role=role,
                         available_roles=available_roles,
                         permissions=permissions,
                         ldap_groups=ldap_groups)

@bp.route('/roles/<int:role_id>/delete_web')
@login_required
@requires_permission('admin_roles_access', 'delete')
@track_activity
def delete_role_web(role_id):
    """Delete a role if it can be safely removed (web route)."""
    role = Role.query.get_or_404(role_id)
    
    if not role.can_be_deleted():
        flash('This role cannot be deleted. It may be a system role or have users/children.', 'warning')
        return redirect(url_for('admin.roles'))
    
    try:
        db.session.delete(role)
        db.session.commit()
        flash(f'Role "{role.name}" deleted successfully.', 'success')
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
    
    # Get activities related to this role
    activities = UserActivity.query.filter(
        UserActivity.activity.like(f'%{role.name}%')
    ).order_by(UserActivity.timestamp.desc()).limit(20).all()
    
    # Get users not in this role for the add member form
    available_users = User.query.filter(~User.roles.contains(role)).all()
    
    return render_template('admin/role_members.html',
                         role=role,
                         activities=activities,
                         available_users=available_users)

# Role Management API Endpoints
@bp.route('/roles/tree')
@login_required
@requires_permission('admin_roles_access', 'read')
def roles_tree():
    """Get the complete role hierarchy as JSON."""
    return jsonify(Role.get_role_tree())

@bp.route('/roles/<int:role_id>/permissions')
@login_required
@requires_permission('admin_roles_access', 'read')
def get_role_permissions(role_id):
    """Get permissions for a specific role."""
    role = Role.query.get_or_404(role_id)
    permissions = role.get_permissions(include_parent=True)
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'description': p.description,
        'category': p.category
    } for p in permissions])

@bp.route('/roles/<int:role_id>/update', methods=['POST'])
@login_required
@requires_permission('admin_roles_access', 'write')
def update_role_partial(role_id):
    """Update specific fields of a role (for auto-save)."""
    role = Role.query.get_or_404(role_id)
    
    try:
        # Update basic info
        if 'name' in request.form:
            role.name = request.form['name']
        if 'description' in request.form:
            role.description = request.form['description']
        if 'notes' in request.form:
            role.notes = request.form['notes']
        if 'icon' in request.form:
            role.icon = request.form['icon']
        if 'is_system_role' in request.form:
            role.is_system_role = bool(request.form['is_system_role'])
        if 'weight' in request.form:
            role.weight = int(request.form['weight'])
        
        # Update parent role
        if 'parent_id' in request.form:
            new_parent_id = request.form['parent_id']
            role.parent_id = int(new_parent_id) if new_parent_id else None
        
        # Update permissions
        if 'permissions[]' in request.form:
            permission_ids = [int(pid) for pid in request.form.getlist('permissions[]')]
            permissions = Permission.query.filter(Permission.id.in_(permission_ids)).all()
            role.permissions = permissions
        
        # Update LDAP settings
        if 'ldap_groups[]' in request.form:
            role.ldap_groups = request.form.getlist('ldap_groups[]')
        if 'auto_sync' in request.form:
            role.auto_sync = bool(request.form['auto_sync'])
        
        role.updated_by = current_user.username
        role.updated_at = datetime.utcnow()
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Role updated successfully'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating role: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@bp.route('/roles/validate-name')
@login_required
@requires_permission('admin_roles_access', 'read')
def validate_role_name():
    """Check if a role name is available."""
    name = request.args.get('name', '').strip()
    role_id = request.args.get('role_id')
    
    if not name:
        return jsonify({
            'valid': False,
            'message': 'Role name is required'
        })
    
    # Check if name exists
    existing_role = Role.query.filter(Role.name == name).first()
    if existing_role and str(existing_role.id) != role_id:
        return jsonify({
            'valid': False,
            'message': 'This role name is already taken'
        })
    
    return jsonify({
        'valid': True,
        'message': 'Role name is available'
    })

@bp.route('/roles/check-circular-dependency')
@login_required
@requires_permission('admin_roles_access', 'read')
def check_circular_dependency():
    """Check if a parent-child relationship would create a circular dependency."""
    role_id = request.args.get('role_id')
    parent_id = request.args.get('parent_id')
    
    if not role_id or not parent_id:
        return jsonify({
            'valid': False,
            'message': 'Both role_id and parent_id are required'
        })
    
    role = Role.query.get_or_404(int(role_id))
    potential_parent = Role.query.get_or_404(int(parent_id))
    
    if potential_parent.is_descendant_of(role):
        return jsonify({
            'valid': False,
            'message': 'This would create a circular dependency'
        })
    
    return jsonify({
        'valid': True,
        'message': 'Valid parent-child relationship'
    })

@bp.route('/roles/<int:role_id>/sync-ldap')
@login_required
@requires_permission('admin_roles_access', 'write')
@track_activity
def sync_role_ldap(role_id):
    """Manually trigger LDAP synchronization for a role."""
    role = Role.query.get_or_404(role_id)
    
    try:
        result = role.sync_ldap_groups()
        flash(f'LDAP synchronization completed. Added: {result["added"]}, Removed: {result["removed"]}', 'success')
    except Exception as e:
        logger.error(f"Error syncing LDAP for role {role.id}: {e}")
        flash('Error synchronizing with LDAP. Please try again.', 'danger')
    
    return redirect(url_for('admin.role_members', role_id=role.id))

@bp.route('/roles/<int:role_id>/sync-status')
@login_required
@requires_permission('admin_roles_access', 'read')
def get_role_sync_status(role_id):
    """Get LDAP synchronization status for a role."""
    role = Role.query.get_or_404(role_id)
    return jsonify(role.get_ldap_sync_status())

@bp.route('/roles/<int:role_id>/members/add', methods=['POST'])
@login_required
@requires_permission('admin_roles_access', 'write')
@track_activity
def add_role_member(role_id):
    """Add a user to a role."""
    role = Role.query.get_or_404(role_id)
    user_id = request.form.get('user_id')
    
    if not user_id:
        return jsonify({
            'success': False,
            'message': 'No user selected'
        }), 400
    
    try:
        user = User.query.get_or_404(user_id)
        if role not in user.roles:
            user.roles.append(role)
            db.session.commit()
            return jsonify({
                'success': True,
                'message': f'Added {user.username} to role {role.name}'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'User already has this role'
            }), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding member to role: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@bp.route('/roles/<int:role_id>/members/remove', methods=['POST'])
@login_required
@requires_permission('admin_roles_access', 'write')
@track_activity
def remove_role_member(role_id):
    """Remove a user from a role."""
    role = Role.query.get_or_404(role_id)
    user_id = request.form.get('user_id')
    
    if not user_id:
        return jsonify({
            'success': False,
            'message': 'No user specified'
        }), 400
    
    try:
        user = User.query.get_or_404(user_id)
        if role in user.roles:
            user.roles.remove(role)
            db.session.commit()
            return jsonify({
                'success': True,
                'message': f'Removed {user.username} from role {role.name}'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'User does not have this role'
            }), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error removing member from role: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
