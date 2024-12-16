"""Route management functionality for admin module."""

from flask import render_template, flash, redirect, url_for, request, jsonify, current_app
from flask_login import login_required, current_user
from app.utils.enhanced_rbac import requires_permission
from app.models import Role, PageRouteMapping, NavigationCategory
from app import db
from app.routes.admin import admin_bp as bp
from datetime import datetime
import logging
from app.utils.activity_tracking import track_activity

logger = logging.getLogger(__name__)

@bp.route('/routes')
@login_required
@requires_permission('admin_routes_access', 'read')
@track_activity
def routes():
    """List all route mappings."""
    mappings = PageRouteMapping.query.all()
    return render_template('admin/routes.html', mappings=mappings)

@bp.route('/routes/new', methods=['GET', 'POST'])
@login_required
@requires_permission('admin_routes_access', 'write')
@track_activity
def new_route():
    """Create a new route mapping."""
    if request.method == 'POST':
        try:
            mapping = PageRouteMapping(
                route=request.form['route'],
                page_name=request.form['page_name'],
                description=request.form.get('description'),
                category_id=request.form.get('category_id'),
                icon=request.form.get('icon', 'fa-link'),
                weight=int(request.form.get('weight', 0)),
                created_by=current_user.username
            )
            db.session.add(mapping)
            db.session.commit()
            flash(f'Route "{mapping.page_name}" created successfully.', 'success')
            return redirect(url_for('admin.routes'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating route: {e}")
            flash('Error creating route. Please try again.', 'danger')
    
    categories = NavigationCategory.query.all()
    return render_template('admin/route_form.html',
                         mapping=None,
                         categories=categories)

@bp.route('/routes/<int:route_id>/edit', methods=['GET', 'POST'])
@login_required
@requires_permission('admin_routes_access', 'write')
@track_activity
def edit_route(route_id):
    """Edit an existing route mapping."""
    mapping = PageRouteMapping.query.get_or_404(route_id)
    
    if request.method == 'POST':
        try:
            mapping.route = request.form['route']
            mapping.page_name = request.form['page_name']
            mapping.description = request.form.get('description')
            mapping.category_id = request.form.get('category_id')
            mapping.icon = request.form.get('icon', 'fa-link')
            mapping.weight = int(request.form.get('weight', 0))
            mapping.updated_by = current_user.username
            mapping.updated_at = datetime.utcnow()
            
            # Update allowed roles
            if request.form.getlist('allowed_roles[]'):
                role_ids = [int(rid) for rid in request.form.getlist('allowed_roles[]')]
                roles = Role.query.filter(Role.id.in_(role_ids)).all()
                mapping.allowed_roles = roles
            else:
                mapping.allowed_roles = []
            
            db.session.commit()
            flash(f'Route "{mapping.page_name}" updated successfully.', 'success')
            return redirect(url_for('admin.routes'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating route: {e}")
            flash('Error updating route. Please try again.', 'danger')
    
    categories = NavigationCategory.query.all()
    roles = Role.query.all()
    return render_template('admin/route_form.html',
                         mapping=mapping,
                         categories=categories,
                         roles=roles)

@bp.route('/routes/<int:route_id>/delete')
@login_required
@requires_permission('admin_routes_access', 'delete')
@track_activity
def delete_route(route_id):
    """Delete a route mapping."""
    mapping = PageRouteMapping.query.get_or_404(route_id)
    
    try:
        name = mapping.page_name
        db.session.delete(mapping)
        db.session.commit()
        flash(f'Route "{name}" deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting route: {e}")
        flash('Error deleting route. Please try again.', 'danger')
    
    return redirect(url_for('admin.routes'))

@bp.route('/routes/list')
@login_required
@requires_permission('admin_routes_access', 'read')
def get_routes():
    """Get list of available routes for route mapping."""
    # Get all registered routes
    routes = []
    for rule in current_app.url_map.iter_rules():
        if not rule.endpoint.startswith('static'):
            routes.append({
                'endpoint': rule.endpoint,
                'route': rule.rule,
                'methods': list(rule.methods)
            })
    return jsonify(routes)
