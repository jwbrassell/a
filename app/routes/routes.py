from flask import (
    render_template, redirect, url_for, flash,
    request, session, current_app
)
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFError
import logging
import os
from datetime import datetime, timedelta

from app.extensions import db
from app.models import User, UserActivity, UserPreference
from app.forms import LoginForm
from app.mock_ldap import authenticate_ldap
from app.logging_utils import log_page_visit
from app.utils.activity_tracking import track_activity

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_base_routes(app):
    """Initialize base routes without admin routes"""
    try:
        from flask import Blueprint
        bp = Blueprint('main', __name__)
        if init_routes(bp):
            app.register_blueprint(bp)
            return bp
        return None
    except Exception as e:
        logger.error(f"Failed to initialize base routes: {e}")
        return None

def init_routes(bp):
    """Initialize routes with blueprint"""
    try:
        logger.info("Starting route initialization")
        
        # Add template context processor
        @bp.context_processor
        def inject_now():
            return {'now': datetime.utcnow()}
        
        # Define utility functions with error handling
        def safe_log_activity(user, activity):
            """Safely log user activity to database."""
            try:
                user_activity = UserActivity(
                    user_id=user.id if user else None,
                    username=user.username if user else 'Anonymous',
                    activity=activity
                )
                db.session.add(user_activity)
                db.session.commit()
            except Exception as e:
                logger.error(f"Failed to log activity: {e}")
                db.session.rollback()

        def safe_init_user_preferences(user):
            """Safely initialize default preferences for a user."""
            try:
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
            except Exception as e:
                logger.error(f"Failed to initialize user preferences: {e}")
                db.session.rollback()

        # Authentication Routes
        @bp.route('/login', methods=['GET', 'POST'])
        def login():
            """Handle user login with both LDAP and local authentication."""
            if current_user.is_authenticated:
                return redirect(url_for('main.index'))

            form = LoginForm()
            if form.validate_on_submit():
                try:
                    username = form.username.data
                    password = form.password.data

                    # First try local authentication
                    user = User.query.filter_by(username=username).first()
                    if user and user.password_hash and user.check_password(password):
                        login_user(user)
                        session['_creation_time'] = datetime.utcnow().timestamp()
                        session.permanent = True
                        safe_init_user_preferences(user)
                        safe_log_activity(user, 'Logged in (local auth)')
                        next_page = session.pop('next_page', None)
                        return redirect(next_page or url_for('main.index'))

                    # Try LDAP auth
                    user_info = authenticate_ldap(username, password)
                    if user_info:
                        user = User.query.filter_by(username=username).first()
                        if not user:
                            user = User(
                                username=user_info['username'],
                                employee_number=user_info.get('employee_number'),
                                name=user_info.get('name'),
                                email=user_info.get('email'),
                                vzid=user_info.get('vzid')
                            )
                            db.session.add(user)
                            db.session.commit()
                            safe_init_user_preferences(user)

                        login_user(user)
                        session['_creation_time'] = datetime.utcnow().timestamp()
                        session.permanent = True
                        session['user_info'] = user_info
                        safe_log_activity(user, 'Logged in (LDAP)')
                        next_page = session.pop('next_page', None)
                        return redirect(next_page or url_for('main.index'))

                    flash('Invalid username or password', 'error')
                except Exception as e:
                    logger.error(f"Login error: {e}")
                    flash('An error occurred during login', 'error')
                    db.session.rollback()

            return render_template('login.html', form=form)

        @bp.route('/logout')
        @login_required
        def logout():
            """Handle user logout."""
            try:
                safe_log_activity(current_user, 'Logged out')
                logout_user()
                session.clear()
                flash('You have been logged out.', 'info')
            except Exception as e:
                logger.error(f"Logout error: {e}")
                flash('An error occurred during logout', 'error')
            return redirect(url_for('main.login'))

        @bp.route('/')
        @bp.route('/index')
        def index():
            """Display main index page."""
            if not current_user.is_authenticated:
                return redirect(url_for('main.login'))
            try:
                safe_log_activity(current_user, 'Visited index page')
            except Exception as e:
                logger.error(f"Index page error: {e}")
            return render_template('index.html')

        @bp.route('/ohshit')
        @login_required
        def ohshit():
            """Display all accessible pages."""
            try:
                safe_log_activity(current_user, 'Visited ohshit page')
            except Exception as e:
                logger.error(f"Ohshit page error: {e}")
            return render_template('ohshit.html')

        # Error Handlers
        @bp.errorhandler(CSRFError)
        def handle_csrf_error(e):
            """Handle CSRF token errors."""
            try:
                if current_user.is_authenticated:
                    safe_log_activity(current_user, 'CSRF token error')
            except Exception as err:
                logger.error(f"CSRF error handler error: {err}")
            flash('The form has expired. Please try again.', 'error')
            return render_template('error.html', 
                                error_title='CSRF Token Error',
                                error_message='The form has expired. Please try again.'), 400

        @bp.errorhandler(400)
        def bad_request_error(e):
            """Handle 400 Bad Request errors."""
            try:
                if current_user.is_authenticated:
                    safe_log_activity(current_user, f'Bad request: {request.path}')
                    flash('Your request could not be processed.', 'warning')
                    return render_template('400.html'), 400
                session['next_page'] = request.url
                flash('Please log in to continue.', 'info')
            except Exception as err:
                logger.error(f"400 error handler error: {err}")
            return redirect(url_for('main.login'))

        @bp.errorhandler(403)
        def forbidden_error(e):
            """Handle 403 Forbidden errors."""
            try:
                if current_user.is_authenticated:
                    safe_log_activity(current_user, f'Forbidden: {request.path}')
                    flash("Access denied.", 'warning')
                    return render_template('403.html'), 403
                session['next_page'] = request.url
                flash('Please log in to access this page.', 'info')
            except Exception as err:
                logger.error(f"403 error handler error: {err}")
            return redirect(url_for('main.login'))

        @bp.errorhandler(404)
        def page_not_found(e):
            """Handle 404 errors."""
            try:
                if current_user.is_authenticated:
                    safe_log_activity(current_user, f'Not found: {request.path}')
                    flash('Page not found.', 'warning')
                    return render_template('404.html'), 404
                session['next_page'] = request.url
                flash('Please log in to continue.', 'info')
            except Exception as err:
                logger.error(f"404 error handler error: {err}")
            return redirect(url_for('main.login'))

        @bp.errorhandler(500)
        def internal_server_error(e):
            """Handle 500 errors."""
            try:
                db.session.rollback()
                error_msg = str(e)
                logger.error(f"Internal Server Error: {error_msg}")
                if current_user.is_authenticated:
                    safe_log_activity(current_user, f'Server error: {error_msg}')
            except Exception as err:
                logger.error(f"500 error handler error: {err}")
            return render_template('500.html'), 500

        logger.info("Route initialization completed successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize routes: {e}")
        return False
