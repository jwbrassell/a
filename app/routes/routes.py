from flask import (
    render_template, redirect, url_for, flash,
    request, session, current_app
)
from flask_login import login_user, logout_user, login_required, current_user
import logging
import os
from datetime import datetime, timedelta

from app import db
from app.models import User, UserActivity, UserPreference
from app.forms import LoginForm
from app.mock_ldap import authenticate_ldap
from app.logging_utils import log_page_visit
from app.utils.plugin_manager import PluginManager
from app.utils.init_db import init_roles_and_users
from app.utils.activity_tracking import track_activity

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_routes(bp):
    """Initialize routes with blueprint"""
    
    def log_activity(user, activity):
        """Log user activity to database."""
        user_activity = UserActivity(
            user_id=user.id if user else None,
            username=user.username if user else 'Anonymous',
            activity=activity
        )
        db.session.add(user_activity)
        db.session.commit()

    # Request Handlers for Page Visit Logging
    @bp.before_request
    def before_request():
        """Log page visit attempt."""
        return log_page_visit()

    @bp.after_request
    def after_request(response):
        """Log page visit result after processing."""
        return log_page_visit(response)

    def init_user_preferences(user):
        """Initialize default preferences for a user."""
        default_preferences = {
            'theme': 'light',
            'notifications': 'true',
            'language': 'en'
        }
        
        for key, value in default_preferences.items():
            if not UserPreference.query.filter_by(user_id=user.id, key=key).first():
                pref = UserPreference(user_id=user.id, key=key, value=str(value))
                db.session.add(pref)
        db.session.commit()

    # Authentication Routes
    @bp.route('/login', methods=['GET', 'POST'])
    @track_activity
    def login():
        """Handle user login with both LDAP and local authentication."""
        if current_user.is_authenticated:
            return redirect(url_for('main.index'))

        form = LoginForm()
        if form.validate_on_submit():
            username = form.username.data
            password = form.password.data

            # First try local authentication for development users
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                # Set session creation time
                session['_creation_time'] = datetime.utcnow().timestamp()
                session.permanent = True  # Use permanent session with lifetime from config
                
                # Initialize default preferences if not exists
                init_user_preferences(user)
                
                flash(f'Welcome, {user.name}!', 'success')
                log_activity(user, 'Logged in (local auth)')
                next_page = session.pop('next_page', None)
                return redirect(next_page or url_for('main.index'))

            # If local auth fails, try LDAP
            user_info = authenticate_ldap(username, password)
            if user_info:
                user = User.query.filter_by(username=username).first()

                if not user:
                    # Create new user
                    user = User(
                        username=user_info['username'],
                        employee_number=user_info['employee_number'],
                        name=user_info['name'],
                        email=user_info['email'],
                        vzid=user_info['vzid']
                    )
                    db.session.add(user)
                    db.session.commit()
                    # Initialize default preferences for new user
                    init_user_preferences(user)
                else:
                    # Update existing user information
                    updated = False
                    update_fields = [
                        ('employee_number', 'employee_number'),
                        ('name', 'name'),
                        ('email', 'email'),
                        ('vzid', 'vzid')
                    ]

                    for db_field, info_field in update_fields:
                        if getattr(user, db_field) != user_info[info_field]:
                            setattr(user, db_field, user_info[info_field])
                            updated = True

                    if updated:
                        db.session.commit()

                    # Initialize preferences if not exists
                    init_user_preferences(user)

                login_user(user)
                # Set session creation time
                session['_creation_time'] = datetime.utcnow().timestamp()
                session.permanent = True  # Use permanent session with lifetime from config
                session['user_info'] = user_info
                flash(f'Welcome, {user.name}!', 'success')
                log_activity(user, 'Logged in (LDAP)')

                next_page = session.pop('next_page', None)
                return redirect(next_page or url_for('main.index'))

            flash('Invalid username or password', 'error')

        return render_template('login.html', form=form)

    @bp.route('/logout')
    @login_required
    @track_activity
    def logout():
        """Handle user logout."""
        log_activity(current_user, 'Logged out')
        logout_user()
        # Clear the session
        session.clear()
        flash('You have been logged out. Please log in again to continue.', 'info')
        return redirect(url_for('main.login'))

    # General Routes
    @bp.route('/')
    @bp.route('/index')
    @track_activity
    def index():
        """Display main index page."""
        if not current_user.is_authenticated:
            return redirect(url_for('main.login'))
        
        # Get plugin metadata from plugin manager
        plugin_manager = current_app.config.get('PLUGIN_MANAGER')
        plugins = {}
        if plugin_manager:
            try:
                plugins = plugin_manager.get_all_plugin_metadata()
                # Filter out plugins that don't have valid routes
                from app.utils.route_manager import route_to_endpoint
                plugins = {
                    name: meta for name, meta in plugins.items()
                    if route_to_endpoint(f"{name}.index")  # Only keep plugins with valid index routes
                }
            except Exception as e:
                logger.error(f"Error getting plugin metadata: {str(e)}")
        
        log_activity(current_user, 'Visited index page')
        return render_template('index.html', plugins=plugins)

    # Error Handlers
    @bp.errorhandler(400)
    def bad_request_error(e):
        """Handle 400 Bad Request errors."""
        if current_user.is_authenticated:
            log_activity(current_user, f'Encountered bad request error: {request.path}')
            flash('Your request could not be processed.', 'warning')
            return render_template('400.html'), 400
        else:
            session['next_page'] = request.url
            flash('Please log in to continue.', 'info')
            return redirect(url_for('main.login'))

    @bp.errorhandler(403)
    def forbidden_error(e):
        """Handle 403 Forbidden errors."""
        if current_user.is_authenticated:
            log_activity(current_user, f'Attempted to access forbidden page: {request.path}')
            flash("Sorry, you don't have access to that page.", 'warning')
            return render_template('403.html'), 403
        else:
            session['next_page'] = request.url
            flash('Please log in to access this page.', 'info')
            return redirect(url_for('main.login'))

    @bp.errorhandler(404)
    def page_not_found(e):
        """Handle 404 errors."""
        if current_user.is_authenticated:
            log_activity(current_user, f'Attempted to access non-existent page: {request.path}')
            flash('The page you requested does not exist.', 'warning')
            return render_template('404.html'), 404
        else:
            session['next_page'] = request.url
            flash('Please log in to continue.', 'info')
            return redirect(url_for('main.login'))

    @bp.errorhandler(500)
    def internal_server_error(e):
        """Handle 500 errors."""
        db.session.rollback()
        error_msg = str(e)
        logger.error(f"Internal Server Error: {error_msg}")
        if current_user.is_authenticated:
            log_activity(current_user, f'Encountered server error: {error_msg}')
        return render_template('500.html'), 500
