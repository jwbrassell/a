"""Profile routes module."""
from flask import Blueprint, render_template, request, jsonify, current_app, send_file
from flask_login import current_user, login_required
from app.extensions import db
from app.utils.cache_manager import cached
from sqlalchemy import desc
from app.models.user import User
from app.models.activity import UserActivity
from datetime import datetime, timedelta
import io

bp = Blueprint('profile', __name__)

@bp.route('/')
@login_required
def profile():
    """Display user profile."""
    return render_template('profile/profile.html')

@bp.route('/avatar/<int:user_id>')
@login_required
def get_avatar(user_id):
    """Get user avatar."""
    user = User.query.get_or_404(user_id)
    avatar_data, mimetype = user.get_avatar_data()
    
    if not avatar_data:
        return send_file(
            current_app.config['DEFAULT_AVATAR_PATH'],
            mimetype='image/jpeg'
        )
    
    return send_file(
        io.BytesIO(avatar_data),
        mimetype=mimetype
    )

@bp.route('/activities/data')
@login_required
@cached(timeout=60, key_prefix='user_activities')
def get_activities():
    """Get user activities."""
    # Get activities from the last 30 days
    since = datetime.utcnow() - timedelta(days=30)
    
    activities = UserActivity.query.filter(
        UserActivity.user_id == current_user.id,
        UserActivity.timestamp >= since
    ).order_by(desc(UserActivity.timestamp)).limit(50).all()
    
    return jsonify([{
        'activity': activity.activity,
        'timestamp': activity.timestamp.isoformat(),
        'details': activity.details
    } for activity in activities])

@bp.route('/preferences', methods=['GET'])
@login_required
def get_preferences():
    """Get user preferences."""
    return jsonify({
        'theme': current_user.get_preference('theme', 'light'),
        'notifications': current_user.get_preference('notifications', True),
        'language': current_user.get_preference('language', 'en')
    })

@bp.route('/preferences', methods=['POST'])
@login_required
def update_preferences():
    """Update user preferences."""
    data = request.get_json()
    
    if 'theme' in data:
        current_user.set_preference('theme', data['theme'])
    if 'notifications' in data:
        current_user.set_preference('notifications', data['notifications'])
    if 'language' in data:
        current_user.set_preference('language', data['language'])
    
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/avatar', methods=['POST'])
@login_required
def update_avatar():
    """Update user avatar."""
    if 'avatar' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
        
    file = request.files['avatar']
    if not file.filename:
        return jsonify({'error': 'No file selected'}), 400
        
    if not file.content_type.startswith('image/'):
        return jsonify({'error': 'File must be an image'}), 400
    
    try:
        current_user.set_avatar(file.read(), file.content_type)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        current_app.logger.error(f"Error updating avatar: {e}")
        return jsonify({'error': 'Failed to update avatar'}), 500
