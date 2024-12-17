"""Navigation category management functionality for admin module."""

from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from app.utils.enhanced_rbac import requires_permission
from app.models import NavigationCategory
from app import db
from app.routes.admin import admin_bp as bp
from datetime import datetime
import logging
from app.utils.activity_tracking import track_activity

logger = logging.getLogger(__name__)

@bp.route('/navigation/categories')
@login_required
@requires_permission('admin_routes_access', 'read')
@track_activity
def navigation_categories():
    """List all navigation categories."""
    categories = NavigationCategory.query.order_by(NavigationCategory.weight).all()
    return render_template('admin/navigation_categories.html', categories=categories)

@bp.route('/navigation/categories/save', methods=['POST'])
@login_required
@requires_permission('admin_routes_access', 'write')
@track_activity
def save_category():
    """Create or update a navigation category."""
    category_id = request.form.get('category_id')
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    try:
        if category_id:
            # Update existing category
            category = NavigationCategory.query.get_or_404(category_id)
            category.name = request.form['name']
            category.icon = request.form.get('icon', 'fa-folder')
            category.description = request.form.get('description')
            category.weight = int(request.form.get('weight', 0))
            category.updated_by = current_user.username
            category.updated_at = datetime.utcnow()
            message = f'Category "{category.name}" updated successfully.'
        else:
            # Create new category
            category = NavigationCategory(
                name=request.form['name'],
                icon=request.form.get('icon', 'fa-folder'),
                description=request.form.get('description'),
                weight=int(request.form.get('weight', 0)),
                created_by=current_user.username
            )
            db.session.add(category)
            message = f'Category "{category.name}" created successfully.'
        
        db.session.commit()

        if is_ajax:
            return jsonify({
                'id': category.id,
                'name': category.name,
                'icon': category.icon,
                'message': message
            })
        
        flash(message, 'success')
        return redirect(url_for('admin.navigation_categories'))
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving category: {e}")
        error_message = 'Error saving category. Please try again.'
        
        if is_ajax:
            return jsonify({'error': error_message}), 400
        
        flash(error_message, 'danger')
        return redirect(url_for('admin.navigation_categories'))

@bp.route('/navigation/categories/<int:category_id>/delete')
@login_required
@requires_permission('admin_routes_access', 'delete')
@track_activity
def delete_category(category_id):
    """Delete a navigation category."""
    category = NavigationCategory.query.get_or_404(category_id)
    
    if not category.can_be_deleted():
        flash('Cannot delete category that has routes assigned to it.', 'danger')
        return redirect(url_for('admin.navigation_categories'))
    
    try:
        name = category.name
        db.session.delete(category)
        db.session.commit()
        flash(f'Category "{name}" deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting category: {e}")
        flash('Error deleting category. Please try again.', 'danger')
    
    return redirect(url_for('admin.navigation_categories'))

@bp.route('/navigation/categories/list')
@login_required
@requires_permission('admin_routes_access', 'read')
def get_categories():
    """Get list of available categories."""
    categories = NavigationCategory.query.order_by(NavigationCategory.name).all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'icon': c.icon
    } for c in categories])
