"""User management functionality for admin module."""

from flask import render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from app.utils.enhanced_rbac import requires_permission
from app.models import User, Role
from app.extensions import db
from app.routes.admin import admin_bp as bp
from datetime import datetime
import logging
from werkzeug.security import generate_password_hash
from app.utils.activity_tracking import track_activity
import os
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

@bp.route('/users')
@login_required
@requires_permission('admin_users_access', 'read')
@track_activity
def users():
    """List all users and manage their roles."""
    users = User.query.all()
    all_roles = Role.query.all()
    return render_template('admin/users.html', users=users, all_roles=all_roles)

@bp.route('/users/new', methods=['GET', 'POST'])
@login_required
@requires_permission('admin_users_access', 'write')
@track_activity
def new_user():
    """Create a new user."""
    if request.method == 'POST':
        try:
            # Create new user
            user = User(
                username=request.form['username'],
                email=request.form['email'],
                full_name=request.form.get('full_name', ''),
                is_active=bool(request.form.get('is_active')),
                created_by=current_user.username
            )
            user.set_password(request.form['password'])

            # Handle avatar upload
            if 'avatar' in request.files:
                file = request.files['avatar']
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                    user.avatar_url = url_for('static', filename=f'uploads/{filename}')

            # Assign roles
            if request.form.getlist('roles[]'):
                role_ids = [int(rid) for rid in request.form.getlist('roles[]')]
                roles = Role.query.filter(Role.id.in_(role_ids)).all()
                user.roles = roles

            db.session.add(user)
            db.session.commit()
            flash(f'User "{user.username}" created successfully.', 'success')
            return redirect(url_for('admin.users'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating user: {e}")
            flash('Error creating user. Please try again.', 'danger')

    roles = Role.query.all()
    return render_template('admin/user_form.html', user=None, roles=roles)

@bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@requires_permission('admin_users_access', 'write')
@track_activity
def edit_user(user_id):
    """Edit an existing user."""
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        try:
            user.username = request.form['username']
            user.email = request.form['email']
            user.full_name = request.form.get('full_name', '')
            user.is_active = bool(request.form.get('is_active'))
            user.updated_by = current_user.username
            user.updated_at = datetime.utcnow()

            # Handle avatar upload
            if 'avatar' in request.files:
                file = request.files['avatar']
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                    # Remove old avatar if exists
                    if user.avatar_url:
                        old_filename = os.path.basename(user.avatar_url)
                        old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], old_filename)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                    user.avatar_url = url_for('static', filename=f'uploads/{filename}')

            # Update roles
            if request.form.getlist('roles[]'):
                role_ids = [int(rid) for rid in request.form.getlist('roles[]')]
                roles = Role.query.filter(Role.id.in_(role_ids)).all()
                user.roles = roles
            else:
                user.roles = []

            db.session.commit()
            flash(f'User "{user.username}" updated successfully.', 'success')
            return redirect(url_for('admin.users'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating user: {e}")
            flash('Error updating user. Please try again.', 'danger')

    roles = Role.query.all()
    return render_template('admin/user_form.html', user=user, roles=roles)

@bp.route('/users/<int:user_id>/delete')
@login_required
@requires_permission('admin_users_access', 'delete')
@track_activity
def delete_user(user_id):
    """Delete a user."""
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin.users'))
    
    try:
        # Remove avatar file if exists
        if user.avatar_url:
            filename = os.path.basename(user.avatar_url)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(file_path):
                os.remove(file_path)
        
        username = user.username
        db.session.delete(user)
        db.session.commit()
        flash(f'User "{username}" deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting user: {e}")
        flash('Error deleting user. Please try again.', 'danger')
    
    return redirect(url_for('admin.users'))

@bp.route('/users/<int:user_id>/roles', methods=['POST'])
@login_required
@requires_permission('admin_users_access', 'write')
@track_activity
def update_user_roles(user_id):
    """Update user roles."""
    user = User.query.get_or_404(user_id)
    
    try:
        if request.form.getlist('roles[]'):
            role_ids = [int(rid) for rid in request.form.getlist('roles[]')]
            roles = Role.query.filter(Role.id.in_(role_ids)).all()
            user.roles = roles
        else:
            user.roles = []
        
        user.updated_by = current_user.username
        user.updated_at = datetime.utcnow()
        db.session.commit()
        flash(f'Roles for user "{user.username}" updated successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating user roles: {e}")
        flash('Error updating user roles. Please try again.', 'danger')
    
    return redirect(url_for('admin.users'))
