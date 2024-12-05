"""User profile management plugin."""

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app.utils.plugin_manager import PluginMetadata
from app.utils.activity_tracking import track_activity
from app import db
from app.models import UserActivity, PageVisit
from sqlalchemy import func, desc

# Create the blueprint
bp = Blueprint('profile', __name__,
              template_folder='templates',
              static_folder='static',  # Add static folder like hello plugin
              url_prefix='/profile')

# Define plugin metadata
plugin_metadata = PluginMetadata(
    name="User Profile",  # Full name
    version="1.0.0",
    description="User profile management plugin",
    author="System",
    required_roles=[],  # No specific roles required, just authentication
    icon="fa-user",
    category="User",  # Navigation category
    weight=98  # Position above logout
)

# Define routes
@bp.route('/')
@login_required
@track_activity
def index():
    """User profile page."""
    # Get recent activities
    recent_activities = UserActivity.query.filter_by(user_id=current_user.id)\
        .order_by(UserActivity.timestamp.desc())\
        .limit(10).all()
    
    # Get popular routes
    popular_routes = db.session.query(
        PageVisit.route,
        func.count(PageVisit.id).label('visit_count')
    ).filter_by(user_id=current_user.id)\
    .group_by(PageVisit.route)\
    .order_by(desc('visit_count'))\
    .limit(5).all()
    
    return render_template('profile/index.html', 
                         user=current_user,
                         recent_activities=recent_activities,
                         popular_routes=popular_routes)

@bp.route('/preferences/theme', methods=['POST'])
@login_required
@track_activity
def update_theme():
    """Update user's theme preference."""
    theme = request.json.get('theme')
    if theme not in ['light', 'dark']:
        return jsonify({'error': 'Invalid theme'}), 400
    
    current_user.set_preference('theme', theme)
    
    return jsonify({'success': True, 'theme': theme})
