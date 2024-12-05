from flask import render_template, flash, redirect, url_for, request, jsonify, current_app
from flask_login import login_required, current_user
from app.utils.rbac import requires_roles
from app.models import Role, PageRouteMapping, UserActivity, NavigationCategory
from app import db
from app.plugins.admin import bp
from datetime import datetime, timedelta
import logging
import re
from sqlalchemy import func
from werkzeug.routing import Map

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
    
    # Get recent activities (last 24 hours)
    recent_activities = UserActivity.query.filter(
        UserActivity.timestamp >= datetime.utcnow() - timedelta(days=1)
    ).all()
    
    return render_template('admin/index.html',
                         roles=roles,
                         categories=categories,
                         routes=routes,
                         recent_activities=recent_activities)

# Role Management
@bp.route('/roles')
@login_required
@requires_roles('admin')
def roles():
    """List all roles."""
    roles = Role.query.all()
    return render_template('admin/roles.html', roles=roles)

@bp.route('/roles/new', methods=['GET', 'POST'])
@login_required
@requires_roles('admin')
def new_role():
    """Create a new role."""
    if request.method == 'POST':
        try:
            role = Role(
                name=request.form['name'],
                notes=request.form.get('notes'),
                icon=request.form.get('icon', 'fa-user-shield'),
                created_by=current_user.username
            )
            db.session.add(role)
            db.session.commit()
            
            activity = UserActivity(
                user_id=current_user.id,
                username=current_user.username,
                activity=f"Created new role: {role.name}"
            )
            db.session.add(activity)
            db.session.commit()
            
            flash(f'Role {role.name} created successfully.', 'success')
            return redirect(url_for('admin.roles'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating role: {str(e)}")
            flash('Error creating role.', 'error')
    
    return render_template('admin/role_form.html', role=None)

@bp.route('/roles/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@requires_roles('admin')
def edit_role(id):
    """Edit an existing role."""
    role = Role.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            old_name = role.name
            role.name = request.form['name']
            role.notes = request.form.get('notes')
            role.icon = request.form.get('icon', 'fa-user-shield')
            role.updated_by = current_user.username
            db.session.commit()
            
            activity = UserActivity(
                user_id=current_user.id,
                username=current_user.username,
                activity=f"Updated role: {old_name} -> {role.name}"
            )
            db.session.add(activity)
            db.session.commit()
            
            flash(f'Role {role.name} updated successfully.', 'success')
            return redirect(url_for('admin.roles'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating role: {str(e)}")
            flash('Error updating role.', 'error')
    
    return render_template('admin/role_form.html', role=role)

@bp.route('/roles/<int:id>/delete', methods=['POST'])
@login_required
@requires_roles('admin')
def delete_role(id):
    """Delete a role."""
    role = Role.query.get_or_404(id)
    try:
        name = role.name
        db.session.delete(role)
        
        activity = UserActivity(
            user_id=current_user.id,
            username=current_user.username,
            activity=f"Deleted role: {name}"
        )
        db.session.add(activity)
        db.session.commit()
        
        flash(f'Role {name} deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting role: {str(e)}")
        flash('Error deleting role.', 'error')
    
    return redirect(url_for('admin.roles'))

# Navigation Categories
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
        try:
            category = NavigationCategory(
                name=request.form['name'],
                description=request.form.get('description'),
                icon=request.form.get('icon', 'fa-folder'),
                weight=request.form.get('weight', 0),
                created_by=current_user.username
            )
            db.session.add(category)
            
            activity = UserActivity(
                user_id=current_user.id,
                username=current_user.username,
                activity=f"Created new navigation category: {category.name}"
            )
            db.session.add(activity)
            db.session.commit()
            
            flash(f'Category {category.name} created successfully.', 'success')
            return redirect(url_for('admin.categories'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating category: {str(e)}")
            flash('Error creating category.', 'error')
    
    return render_template('admin/category_form.html', category=None)

@bp.route('/categories/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@requires_roles('admin')
def edit_category(id):
    """Edit an existing navigation category."""
    category = NavigationCategory.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            old_name = category.name
            category.name = request.form['name']
            category.description = request.form.get('description')
            category.icon = request.form.get('icon', 'fa-folder')
            category.weight = request.form.get('weight', 0)
            category.updated_by = current_user.username
            
            activity = UserActivity(
                user_id=current_user.id,
                username=current_user.username,
                activity=f"Updated navigation category: {old_name} -> {category.name}"
            )
            db.session.add(activity)
            db.session.commit()
            
            flash(f'Category {category.name} updated successfully.', 'success')
            return redirect(url_for('admin.categories'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating category: {str(e)}")
            flash('Error updating category.', 'error')
    
    return render_template('admin/category_form.html', category=category)

@bp.route('/categories/<int:id>/delete', methods=['POST'])
@login_required
@requires_roles('admin')
def delete_category(id):
    """Delete a navigation category."""
    category = NavigationCategory.query.get_or_404(id)
    
    if category.routes:
        flash('Cannot delete category that has routes assigned to it.', 'error')
        return redirect(url_for('admin.categories'))
    
    try:
        name = category.name
        db.session.delete(category)
        
        activity = UserActivity(
            user_id=current_user.id,
            username=current_user.username,
            activity=f"Deleted navigation category: {name}"
        )
        db.session.add(activity)
        db.session.commit()
        
        flash(f'Category {name} deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting category: {str(e)}")
        flash('Error deleting category.', 'error')
    
    return redirect(url_for('admin.categories'))

# Route Mapping Management
@bp.route('/routes')
@login_required
@requires_roles('admin')
def routes():
    """List all route mappings."""
    mappings = PageRouteMapping.query.order_by(PageRouteMapping.weight).all()
    return render_template('admin/routes.html', mappings=mappings)

@bp.route('/routes/new', methods=['GET', 'POST'])
@login_required
@requires_roles('admin')
def new_route():
    """Create a new route mapping."""
    if request.method == 'POST':
        try:
            # Check for duplicate page name
            existing_page = PageRouteMapping.query.filter(
                func.lower(PageRouteMapping.page_name) == func.lower(request.form['page_name'])
            ).first()
            if existing_page:
                flash('A page with this name already exists.', 'error')
                return redirect(url_for('admin.new_route'))

            # Handle new category if provided
            category_id = request.form.get('category_id')
            if category_id and not category_id.isdigit():
                # This is a new category name
                category = NavigationCategory(
                    name=category_id,
                    icon=request.form.get('category_icon', 'fa-folder'),
                    created_by=current_user.username
                )
                db.session.add(category)
                db.session.flush()  # Get the ID without committing
                category_id = category.id

            mapping = PageRouteMapping(
                page_name=request.form['page_name'],
                route=request.form['route'],
                icon=request.form.get('icon', 'fa-link'),
                weight=request.form.get('weight', 0),
                category_id=category_id if category_id and category_id.isdigit() else None
            )
            
            # Handle roles
            role_ids = request.form.getlist('roles')
            roles = Role.query.filter(Role.id.in_(role_ids)).all()
            mapping.allowed_roles = roles
            
            db.session.add(mapping)
            
            activity = UserActivity(
                user_id=current_user.id,
                username=current_user.username,
                activity=f"Created new route mapping: {mapping.route}"
            )
            db.session.add(activity)
            db.session.commit()
            
            flash(f'Route mapping created successfully.', 'success')
            return redirect(url_for('admin.routes'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating route mapping: {str(e)}")
            flash('Error creating route mapping.', 'error')
    
    roles = Role.query.all()
    categories = NavigationCategory.query.order_by(NavigationCategory.weight).all()
    return render_template('admin/route_form.html', mapping=None, roles=roles, categories=categories)

@bp.route('/routes/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@requires_roles('admin')
def edit_route(id):
    """Edit an existing route mapping."""
    mapping = PageRouteMapping.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Check for duplicate page name
            existing_page = PageRouteMapping.query.filter(
                func.lower(PageRouteMapping.page_name) == func.lower(request.form['page_name']),
                PageRouteMapping.id != id
            ).first()
            if existing_page:
                flash('A page with this name already exists.', 'error')
                return redirect(url_for('admin.edit_route', id=id))

            # Handle new category if provided
            category_id = request.form.get('category_id')
            if category_id and not category_id.isdigit():
                # This is a new category name
                category = NavigationCategory(
                    name=category_id,
                    icon=request.form.get('category_icon', 'fa-folder'),
                    created_by=current_user.username
                )
                db.session.add(category)
                db.session.flush()  # Get the ID without committing
                category_id = category.id

            old_route = mapping.route
            mapping.page_name = request.form['page_name']
            mapping.route = request.form['route']
            mapping.icon = request.form.get('icon', 'fa-link')
            mapping.weight = request.form.get('weight', 0)
            mapping.category_id = category_id if category_id and category_id.isdigit() else None
            
            # Handle roles
            role_ids = request.form.getlist('roles')
            roles = Role.query.filter(Role.id.in_(role_ids)).all()
            mapping.allowed_roles = roles
            
            activity = UserActivity(
                user_id=current_user.id,
                username=current_user.username,
                activity=f"Updated route mapping: {old_route} -> {mapping.route}"
            )
            db.session.add(activity)
            db.session.commit()
            
            flash(f'Route mapping updated successfully.', 'success')
            return redirect(url_for('admin.routes'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating route mapping: {str(e)}")
            flash('Error updating route mapping.', 'error')
    
    roles = Role.query.all()
    categories = NavigationCategory.query.order_by(NavigationCategory.weight).all()
    return render_template('admin/route_form.html', mapping=mapping, roles=roles, categories=categories)

@bp.route('/routes/<int:id>/delete', methods=['POST'])
@login_required
@requires_roles('admin')
def delete_route(id):
    """Delete a route mapping."""
    mapping = PageRouteMapping.query.get_or_404(id)
    try:
        route = mapping.route
        db.session.delete(mapping)
        
        activity = UserActivity(
            user_id=current_user.id,
            username=current_user.username,
            activity=f"Deleted route mapping: {route}"
        )
        db.session.add(activity)
        db.session.commit()
        
        flash(f'Route mapping deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting route mapping: {str(e)}")
        flash('Error deleting route mapping.', 'error')
    
    return redirect(url_for('admin.routes'))

# Activity Logs
@bp.route('/logs')
@login_required
@requires_roles('admin')
def activity_logs():
    """View activity logs."""
    logs = UserActivity.query.order_by(UserActivity.timestamp.desc()).all()
    return render_template('admin/logs.html', logs=logs)

# Font Awesome Icon Picker API
@bp.route('/api/icons')
@login_required
@requires_roles('admin')
def get_icons():
    """Get list of Font Awesome icons."""
    # This is a small subset of icons, you might want to expand this
    icons = [
        'fa-home', 'fa-user', 'fa-cog', 'fa-wrench', 'fa-chart-bar',
        'fa-users', 'fa-file', 'fa-folder', 'fa-calendar', 'fa-envelope',
        'fa-bell', 'fa-bookmark', 'fa-chart-line', 'fa-clipboard', 'fa-clock',
        'fa-cogs', 'fa-database', 'fa-download', 'fa-upload', 'fa-edit',
        'fa-eye', 'fa-flag', 'fa-gear', 'fa-globe', 'fa-heart',
        'fa-info-circle', 'fa-key', 'fa-link', 'fa-list', 'fa-lock',
        'fa-map', 'fa-paper-plane', 'fa-plus', 'fa-print', 'fa-save',
        'fa-search', 'fa-star', 'fa-table', 'fa-tag', 'fa-trash',
        'fa-user-shield', 'fa-window-maximize', 'fa-wrench'
    ]
    return jsonify(icons)

# Get available routes
@bp.route('/api/routes')
@login_required
@requires_roles('admin')
def get_routes():
    """Get list of available routes."""
    try:
        routes = []
        for rule in current_app.url_map.iter_rules():
            # Skip static files and admin routes
            if not rule.endpoint.startswith('static.') and not rule.endpoint.startswith('admin.'):
                # Convert URL parameters to a readable format
                url = str(rule)
                if '<' in url:  # Has parameters
                    for param in re.findall(r'<([^>]+)>', url):
                        url = url.replace(f'<{param}>', f':{param.split(":")[-1]}')
                
                routes.append({
                    'endpoint': rule.endpoint,
                    'route': url
                })
        
        return jsonify(routes)
    except Exception as e:
        logger.error(f"Error getting routes: {str(e)}")
        return jsonify([]), 500

# Get category icon
@bp.route('/category/<int:id>/icon')
@login_required
@requires_roles('admin')
def get_category_icon(id):
    """Get icon for a category."""
    try:
        category = NavigationCategory.query.get_or_404(id)
        return jsonify({
            'success': True,
            'icon': category.icon
        })
    except Exception as e:
        logger.error(f"Error getting category icon: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
