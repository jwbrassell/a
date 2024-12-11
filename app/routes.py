from flask import (
    Blueprint, render_template, redirect, url_for, flash,
    request, session, current_app
)
from flask_login import login_user, logout_user, login_required, current_user
import logging
import os
from datetime import datetime, timedelta

from app import db
from app.models import User, UserActivity, UserPreference, Session
from app.forms import LoginForm
from app.mock_ldap import authenticate_ldap
from app.logging_utils import log_page_visit
from app.utils.plugin_manager import PluginManager
from app.utils.init_db import init_roles_and_users
from app.utils.activity_tracking import track_activity

main = Blueprint('main', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def register_blueprints(app):
    """Register all blueprints including plugins."""
    # Register main blueprint
    app.register_blueprint(main)
    logger.info("Registered main blueprint")
    
    # Initialize plugin manager and register plugin blueprints
    plugin_manager = PluginManager(app)
    plugins = plugin_manager.load_all_plugins()
    
    # Store plugin manager in app config for access in views
    app.config['PLUGIN_MANAGER'] = plugin_manager
    
    # Register each plugin blueprint
    for blueprint in plugins:
        if blueprint:  # Only register valid blueprints
            try:
                app.register_blueprint(blueprint)
                logger.info(f"Registered plugin blueprint: {blueprint.name}")
            except Exception as e:
                logger.error(f"Failed to register blueprint: {str(e)}")
    
    logger.info(f"Loaded {len([p for p in plugins if p])} plugins successfully")

    # Initialize default roles and users for local development
    with app.app_context():
        init_roles_and_users()

def log_activity(user, activity):
    """Log user activity to database."""
    user_activity = UserActivity(
        user_id=user.id if user else None,
        username=user.username if user else 'Anonymous',
        activity=activity
    )
    db.session.add(user_activity)
    db.session.commit()

def cleanup_expired_sessions():
    """Clean up expired sessions."""
    try:
        now = datetime.utcnow()
        expired_sessions = Session.query.filter(Session.expiry < now).all()
        for session in expired_sessions:
            db.session.delete(session)
        db.session.commit()
    except Exception as e:
        logger.error(f"Error cleaning up expired sessions: {str(e)}")
        db.session.rollback()

# Request Handlers for Page Visit Logging
@main.before_request
def before_request():
    """Log page visit attempt and clean up expired sessions."""
    # Periodically clean up expired sessions
    if not hasattr(before_request, 'last_cleanup'):
        before_request.last_cleanup = datetime.utcnow()
    elif datetime.utcnow() - before_request.last_cleanup > timedelta(hours=1):
        cleanup_expired_sessions()
        before_request.last_cleanup = datetime.utcnow()
    
    return log_page_visit()

@main.after_request
def after_request(response):
    """Log page visit result after processing."""
    return log_page_visit(response)

# Authentication Routes
@main.route('/login', methods=['GET', 'POST'])
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
            
            # Create default preferences if not exists
            if not UserPreference.query.filter_by(user_id=user.id).first():
                prefs = UserPreference(user_id=user.id)
                db.session.add(prefs)
                db.session.commit()
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
                # Create default preferences for new user
                prefs = UserPreference(user_id=user.id)
                db.session.add(prefs)
                db.session.commit()
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

                # Create preferences if not exists
                if not UserPreference.query.filter_by(user_id=user.id).first():
                    prefs = UserPreference(user_id=user.id)
                    db.session.add(prefs)
                    db.session.commit()

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

@main.route('/logout')
@login_required
@track_activity
def logout():
    """Handle user logout."""
    log_activity(current_user, 'Logged out')
    # Clean up user's session
    if session.sid:
        user_session = Session.query.filter_by(sid=session.sid).first()
        if user_session:
            db.session.delete(user_session)
            db.session.commit()
    logout_user()
    session.clear()
    flash('You have been logged out. Please log in again to continue.', 'info')
    return redirect(url_for('main.login'))

# General Routes
@main.route('/')
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
@main.errorhandler(400)
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

@main.errorhandler(403)
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

@main.errorhandler(404)
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

@main.errorhandler(500)
def internal_server_error(e):
    """Handle 500 errors."""
    db.session.rollback()
    error_msg = str(e)
    logger.error(f"Internal Server Error: {error_msg}")
    if current_user.is_authenticated:
        log_activity(current_user, f'Encountered server error: {error_msg}')
    return render_template('500.html'), 500
