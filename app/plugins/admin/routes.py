from flask import render_template, flash, redirect, url_for, request, jsonify, current_app
from flask_login import login_required, current_user
from app.utils.rbac import requires_roles
from app.models import Role, PageRouteMapping, UserActivity, NavigationCategory, User
from app import db
from app.plugins.admin import bp
from datetime import datetime, timedelta
import logging
import re
from sqlalchemy import func
from werkzeug.routing import Map
import json
import os

logger = logging.getLogger(__name__)

# Dashboard
@bp.route('/')
@login_required
@requires_roles('admin')
def index():
    """Admin dashboard main page."""
    # Get counts for stats
    roles = Role.query.all()
    categories = NavigationCategory.query.all()
    routes = PageRouteMapping.query.all()
    users = User.query.all()
    
    # Get recent activities (last 24 hours)
    recent_activities = UserActivity.query.filter(
        UserActivity.timestamp >= datetime.utcnow() - timedelta(days=1)
    ).all()
    
    return render_template('admin/index.html',
                         roles=roles,
                         categories=categories,
                         routes=routes,
                         recent_activities=recent_activities,
                         users=users)

# User Management
@bp.route('/users')
@login_required
@requires_roles('admin')
def users():
    """List all users and manage their roles."""
    users = User.query.all()
    all_roles = Role.query.all()
    return render_template('admin/users.html', users=users, all_roles=all_roles)

@bp.route('/users/<int:id>/roles', methods=['POST'])
@login_required
@requires_roles('admin')
def update_user_roles(id):
    """Update roles for a user."""
    user = User.query.get_or_404(id)
    try:
        # Get selected role IDs from form
        role_ids = request.form.getlist('roles')
        
        # Get role objects
        new_roles = Role.query.filter(Role.id.in_(role_ids)).all() if role_ids else []
        
        # Update user's roles
        old_roles = set(role.name for role in user.roles)
        user.roles = new_roles
        new_roles_set = set(role.name for role in new_roles)
        
        # Create activity log
        added_roles = new_roles_set - old_roles
        removed_roles = old_roles - new_roles_set
        activity_desc = []
        if added_roles:
            activity_desc.append(f"Added roles: {', '.join(added_roles)}")
        if removed_roles:
            activity_desc.append(f"Removed roles: {', '.join(removed_roles)}")
        
        activity = UserActivity(
            user_id=current_user.id,
            username=current_user.username,
            activity=f"Updated roles for user {user.username}. {' '.join(activity_desc)}"
        )
        db.session.add(activity)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Roles updated successfully for {user.username}.',
            'roles': [{'id': role.id, 'name': role.name} for role in new_roles]
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating user roles: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error updating user roles.'
        }), 500

# Role Management
@bp.route('/roles')
@login_required
@requires_roles('admin')
def roles():
    """List all roles and their permissions."""
    roles = Role.query.all()
    return render_template('admin/roles.html', roles=roles)

@bp.route('/roles/new', methods=['GET', 'POST'])
@login_required
@requires_roles('admin')
def new_role():
    """Create a new role."""
    if request.method == 'POST':
        name = request.form.get('name')
        icon = request.form.get('icon')
        notes = request.form.get('notes')
        
        if Role.query.filter_by(name=name).first():
            flash('A role with that name already exists.', 'danger')
            return redirect(url_for('admin.new_role'))
        
        role = Role(
            name=name,
            icon=icon,
            notes=notes,
            created_by=current_user.username
        )
        
        try:
            db.session.add(role)
            activity = UserActivity(
                user_id=current_user.id,
                username=current_user.username,
                activity=f"Created new role: {name}"
            )
            db.session.add(activity)
            db.session.commit()
            flash('Role created successfully.', 'success')
            return redirect(url_for('admin.roles'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating role: {str(e)}")
            flash('Error creating role.', 'danger')
            
    return render_template('admin/role_form.html', role=None)

@bp.route('/roles/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@requires_roles('admin')
def edit_role(id):
    """Edit an existing role."""
    role = Role.query.get_or_404(id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        icon = request.form.get('icon')
        notes = request.form.get('notes')
        
        existing_role = Role.query.filter_by(name=name).first()
        if existing_role and existing_role.id != id:
            flash('A role with that name already exists.', 'danger')
            return redirect(url_for('admin.edit_role', id=id))
        
        try:
            role.name = name
            role.icon = icon
            role.notes = notes
            role.updated_by = current_user.username
            role.updated_at = datetime.utcnow()
            
            activity = UserActivity(
                user_id=current_user.id,
                username=current_user.username,
                activity=f"Updated role: {name}"
            )
            db.session.add(activity)
            db.session.commit()
            flash('Role updated successfully.', 'success')
            return redirect(url_for('admin.roles'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating role: {str(e)}")
            flash('Error updating role.', 'danger')
            
    return render_template('admin/role_form.html', role=role)

@bp.route('/roles/<int:id>/delete', methods=['POST'])
@login_required
@requires_roles('admin')
def delete_role(id):
    """Delete a role."""
    role = Role.query.get_or_404(id)
    
    try:
        role_name = role.name
        db.session.delete(role)
        
        activity = UserActivity(
            user_id=current_user.id,
            username=current_user.username,
            activity=f"Deleted role: {role_name}"
        )
        db.session.add(activity)
        db.session.commit()
        flash('Role deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting role: {str(e)}")
        flash('Error deleting role.', 'danger')
        
    return redirect(url_for('admin.roles'))

@bp.route('/roles/<int:role_id>/members')
@login_required
@requires_roles('admin')
def role_members(role_id):
    """View members of a role."""
    role = Role.query.get_or_404(role_id)
    # Get users not in this role for the add member form
    available_users = User.query.filter(~User.roles.contains(role)).all()
    return render_template('admin/role_members.html', role=role, available_users=available_users)

@bp.route('/roles/<int:role_id>/members/add', methods=['POST'])
@login_required
@requires_roles('admin')
def add_role_member(role_id):
    """Add a user to a role."""
    role = Role.query.get_or_404(role_id)
    user_id = request.form.get('user_id')
    user = User.query.get_or_404(user_id)
    
    try:
        if role not in user.roles:
            user.roles.append(role)
            activity = UserActivity(
                user_id=current_user.id,
                username=current_user.username,
                activity=f"Added user {user.username} to role {role.name}"
            )
            db.session.add(activity)
            db.session.commit()
            flash(f'Added {user.username} to role {role.name}', 'success')
        else:
            flash(f'User {user.username} is already in role {role.name}', 'warning')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding user to role: {str(e)}")
        flash('Error adding user to role.', 'danger')
    
    return redirect(url_for('admin.role_members', role_id=role_id))

@bp.route('/roles/<int:role_id>/members/<int:user_id>/remove', methods=['POST'])
@login_required
@requires_roles('admin')
def remove_role_member(role_id, user_id):
    """Remove a user from a role."""
    role = Role.query.get_or_404(role_id)
    user = User.query.get_or_404(user_id)
    
    try:
        if role in user.roles:
            user.roles.remove(role)
            activity = UserActivity(
                user_id=current_user.id,
                username=current_user.username,
                activity=f"Removed user {user.username} from role {role.name}"
            )
            db.session.add(activity)
            db.session.commit()
            flash(f'Removed {user.username} from role {role.name}', 'success')
        else:
            flash(f'User {user.username} is not in role {role.name}', 'warning')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error removing user from role: {str(e)}")
        flash('Error removing user from role.', 'danger')
    
    return redirect(url_for('admin.role_members', role_id=role_id))

# Navigation Categories Management
@bp.route('/categories')
@login_required
@requires_roles('admin')
def categories():
    """List all navigation categories."""
    categories = NavigationCategory.query.all()
    return render_template('admin/categories.html', categories=categories)

@bp.route('/categories/new', methods=['GET', 'POST'])
@login_required
@requires_roles('admin')
def new_category():
    """Create a new navigation category."""
    if request.method == 'POST':
        name = request.form.get('name')
        icon = request.form.get('icon')
        description = request.form.get('description')
        weight = request.form.get('weight', type=int)
        
        if NavigationCategory.query.filter_by(name=name).first():
            flash('A category with that name already exists.', 'danger')
            return redirect(url_for('admin.new_category'))
        
        category = NavigationCategory(
            name=name,
            icon=icon,
            description=description,
            weight=weight,
            created_by=current_user.username
        )
        
        try:
            db.session.add(category)
            activity = UserActivity(
                user_id=current_user.id,
                username=current_user.username,
                activity=f"Created new navigation category: {name}"
            )
            db.session.add(activity)
            db.session.commit()
            flash('Category created successfully.', 'success')
            return redirect(url_for('admin.categories'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating category: {str(e)}")
            flash('Error creating category.', 'danger')
            
    return render_template('admin/category_form.html', category=None)

@bp.route('/categories/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@requires_roles('admin')
def edit_category(id):
    """Edit an existing navigation category."""
    category = NavigationCategory.query.get_or_404(id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        icon = request.form.get('icon')
        description = request.form.get('description')
        weight = request.form.get('weight', type=int)
        
        existing_category = NavigationCategory.query.filter_by(name=name).first()
        if existing_category and existing_category.id != id:
            flash('A category with that name already exists.', 'danger')
            return redirect(url_for('admin.edit_category', id=id))
        
        try:
            category.name = name
            category.icon = icon
            category.description = description
            category.weight = weight
            category.updated_by = current_user.username
            category.updated_at = datetime.utcnow()
            
            activity = UserActivity(
                user_id=current_user.id,
                username=current_user.username,
                activity=f"Updated navigation category: {name}"
            )
            db.session.add(activity)
            db.session.commit()
            flash('Category updated successfully.', 'success')
            return redirect(url_for('admin.categories'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating category: {str(e)}")
            flash('Error updating category.', 'danger')
            
    return render_template('admin/category_form.html', category=category)

@bp.route('/categories/<int:id>/delete', methods=['POST'])
@login_required
@requires_roles('admin')
def delete_category(id):
    """Delete a navigation category."""
    category = NavigationCategory.query.get_or_404(id)
    
    if category.routes:
        flash('Cannot delete category that has routes assigned to it.', 'danger')
        return redirect(url_for('admin.categories'))
    
    try:
        category_name = category.name
        db.session.delete(category)
        
        activity = UserActivity(
            user_id=current_user.id,
            username=current_user.username,
            activity=f"Deleted navigation category: {category_name}"
        )
        db.session.add(activity)
        db.session.commit()
        flash('Category deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting category: {str(e)}")
        flash('Error deleting category.', 'danger')
        
    return redirect(url_for('admin.categories'))

# Route Management
@bp.route('/routes')
@login_required
@requires_roles('admin')
def routes():
    """List all route mappings."""
    mappings = PageRouteMapping.query.all()
    return render_template('admin/routes.html', mappings=mappings)

@bp.route('/routes/new', methods=['GET', 'POST'])
@login_required
@requires_roles('admin')
def new_route():
    """Create a new route mapping."""
    if request.method == 'POST':
        page_name = request.form.get('page_name')
        route = request.form.get('route')
        icon = request.form.get('icon')
        weight = request.form.get('weight', type=int)
        nav_type = request.form.get('nav_type')
        category_id = request.form.get('category_id') if nav_type == 'category' else None
        role_ids = request.form.getlist('roles')
        
        if PageRouteMapping.query.filter_by(route=route).first():
            flash('A route mapping for this route already exists.', 'danger')
            return redirect(url_for('admin.new_route'))
        
        mapping = PageRouteMapping(
            page_name=page_name,
            route=route,
            icon=icon,
            weight=weight,
            category_id=category_id
        )
        
        # Add allowed roles
        if role_ids:
            roles = Role.query.filter(Role.id.in_(role_ids)).all()
            mapping.allowed_roles = roles
        
        try:
            db.session.add(mapping)
            activity = UserActivity(
                user_id=current_user.id,
                username=current_user.username,
                activity=f"Created new route mapping: {page_name} -> {route}"
            )
            db.session.add(activity)
            db.session.commit()
            flash('Route mapping created successfully.', 'success')
            return redirect(url_for('admin.routes'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating route mapping: {str(e)}")
            flash('Error creating route mapping.', 'danger')
    
    categories = NavigationCategory.query.all()
    roles = Role.query.all()
    return render_template('admin/route_form.html', mapping=None, categories=categories, roles=roles)

@bp.route('/routes/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@requires_roles('admin')
def edit_route(id):
    """Edit an existing route mapping."""
    mapping = PageRouteMapping.query.get_or_404(id)
    
    if request.method == 'POST':
        page_name = request.form.get('page_name')
        route = request.form.get('route')
        icon = request.form.get('icon')
        weight = request.form.get('weight', type=int)
        nav_type = request.form.get('nav_type')
        category_id = request.form.get('category_id') if nav_type == 'category' else None
        role_ids = request.form.getlist('roles')
        
        existing_mapping = PageRouteMapping.query.filter_by(route=route).first()
        if existing_mapping and existing_mapping.id != id:
            flash('A route mapping for this route already exists.', 'danger')
            return redirect(url_for('admin.edit_route', id=id))
        
        try:
            mapping.page_name = page_name
            mapping.route = route
            mapping.icon = icon
            mapping.weight = weight
            mapping.category_id = category_id
            
            # Update allowed roles
            if role_ids:
                roles = Role.query.filter(Role.id.in_(role_ids)).all()
                mapping.allowed_roles = roles
            else:
                mapping.allowed_roles = []
            
            activity = UserActivity(
                user_id=current_user.id,
                username=current_user.username,
                activity=f"Updated route mapping: {page_name} -> {route}"
            )
            db.session.add(activity)
            db.session.commit()
            flash('Route mapping updated successfully.', 'success')
            return redirect(url_for('admin.routes'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating route mapping: {str(e)}")
            flash('Error updating route mapping.', 'danger')
    
    categories = NavigationCategory.query.all()
    roles = Role.query.all()
    return render_template('admin/route_form.html', mapping=mapping, categories=categories, roles=roles)

@bp.route('/routes/<int:id>/delete', methods=['POST'])
@login_required
@requires_roles('admin')
def delete_route(id):
    """Delete a route mapping."""
    mapping = PageRouteMapping.query.get_or_404(id)
    
    try:
        route_info = f"{mapping.page_name} -> {mapping.route}"
        db.session.delete(mapping)
        
        activity = UserActivity(
            user_id=current_user.id,
            username=current_user.username,
            activity=f"Deleted route mapping: {route_info}"
        )
        db.session.add(activity)
        db.session.commit()
        flash('Route mapping deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting route mapping: {str(e)}")
        flash('Error deleting route mapping.', 'danger')
        
    return redirect(url_for('admin.routes'))

# Activity Logs
@bp.route('/logs')
@login_required
@requires_roles('admin')
def logs():
    """View system activity logs."""
    # Get activities from the last 7 days by default
    activities = UserActivity.query.filter(
        UserActivity.timestamp >= datetime.utcnow() - timedelta(days=7)
    ).order_by(UserActivity.timestamp.desc()).all()
    return render_template('admin/logs.html', activities=activities)

# Icon Management
@bp.route('/icons')
@login_required
@requires_roles('admin')
def get_icons():
    """Get list of available FontAwesome icons."""
    # This is a simplified list - you might want to expand it
    icons = [
        'fa-user', 'fa-users', 'fa-cog', 'fa-wrench', 'fa-folder', 
        'fa-file', 'fa-chart-bar', 'fa-dashboard', 'fa-home',
        'fa-list', 'fa-check', 'fa-times', 'fa-plus', 'fa-minus',
        'fa-edit', 'fa-trash', 'fa-save', 'fa-search', 'fa-envelope',
        'fa-bell', 'fa-calendar', 'fa-clock', 'fa-star', 'fa-heart',
        'fa-bookmark', 'fa-print', 'fa-camera', 'fa-video', 'fa-music',
        'fa-map', 'fa-location-dot', 'fa-link', 'fa-lock', 'fa-unlock',
        'fa-key', 'fa-gear', 'fa-tools', 'fa-database', 'fa-server',
        'fa-network-wired', 'fa-cloud', 'fa-upload', 'fa-download'
    ]
    return jsonify(icons)

# Route List for Select2
@bp.route('/routes/list')
@login_required
@requires_roles('admin')
def get_routes():
    """Get list of available routes for Select2."""
    # Get all registered routes from Flask app
    routes = []
    for rule in current_app.url_map.iter_rules():
        # Skip static files and admin routes
        if not rule.endpoint.startswith('static.') and not rule.endpoint.startswith('admin.'):
            routes.append({
                'endpoint': rule.endpoint,
                'route': rule.rule
            })
    return jsonify(routes)

# Category Icon Endpoint
@bp.route('/category/<int:id>/icon')
@login_required
@requires_roles('admin')
def get_category_icon(id):
    """Get icon for a category."""
    category = NavigationCategory.query.get_or_404(id)
    return jsonify({
        'success': True,
        'icon': category.icon
    })
