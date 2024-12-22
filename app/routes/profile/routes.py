"""Profile routes module."""
from flask import Blueprint, render_template, request, jsonify, current_app, send_file
from flask_login import current_user, login_required
from app.extensions import db
from app.utils.cache_manager import cached
from app.utils.activity_tracking import track_activity
from sqlalchemy import desc
from app.models.user import User
from app.models.activity import UserActivity
from datetime import datetime, timedelta
import io

from app.routes.profile import profile_bp

@profile_bp.route('/')
@login_required
@track_activity
def index():
    """Display user profile."""
    # Get user's recent activities
    activities = UserActivity.query.filter_by(
        user_id=current_user.id
    ).order_by(
        UserActivity.timestamp.desc()
    ).limit(10).all()
    
    return render_template('profile.html', activities=activities)

@profile_bp.route('/avatar/<int:user_id>')
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

@profile_bp.route('/activities/data')
@login_required
def activities_data():
    """Get user activities with server-side processing support."""
    # Get DataTables parameters
    draw = request.args.get('draw', type=int)
    start = request.args.get('start', type=int, default=0)
    length = request.args.get('length', type=int, default=10)
    search = request.args.get('search[value]', type=str, default='')
    order_column = request.args.get('order[0][column]', type=int, default=2)  # Default sort by timestamp
    order_dir = request.args.get('order[0][dir]', type=str, default='desc')
    
    # Get activities from the last 30 days
    since = datetime.utcnow() - timedelta(days=30)
    query = UserActivity.query.filter(
        UserActivity.user_id == current_user.id,
        UserActivity.timestamp >= since
    )
    
    # Apply search if provided
    if search:
        query = query.filter(UserActivity.activity.ilike(f'%{search}%'))
    
    # Get total records before pagination
    total_records = query.count()
    filtered_records = total_records  # Will be different if search is applied
    
    # Apply sorting
    if order_column == 0:  # ID column
        query = query.order_by(desc(UserActivity.id) if order_dir == 'desc' else UserActivity.id)
    elif order_column == 1:  # Activity column
        query = query.order_by(desc(UserActivity.activity) if order_dir == 'desc' else UserActivity.activity)
    else:  # Timestamp column
        query = query.order_by(desc(UserActivity.timestamp) if order_dir == 'desc' else UserActivity.timestamp)
    
    # Apply pagination
    activities = query.offset(start).limit(length).all()
    
    return jsonify({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': filtered_records,
        'data': [{
            'activity': activity.activity,
            'timestamp': activity.timestamp.isoformat(),
            'details': activity.details
        } for activity in activities]
    })

@profile_bp.route('/preferences', methods=['GET'])
@login_required
def get_preferences():
    """Get user preferences."""
    return jsonify({
        'theme': current_user.get_preference('theme', 'light'),
        'notifications': current_user.get_preference('notifications', True),
        'language': current_user.get_preference('language', 'en')
    })

@profile_bp.route('/preferences', methods=['POST'])
@login_required
def update_preferences():
    """Update user preferences."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        if 'theme' in data and data['theme'] in ['light', 'dark']:
            current_user.set_preference('theme', data['theme'])
            db.session.commit()
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Invalid theme value'}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating preferences: {str(e)}")
        return jsonify({'error': 'Failed to update preferences'}), 500

@profile_bp.route('/preferences/theme', methods=['POST'])
@login_required
def update_theme():
    """Update user theme preference."""
    data = request.get_json()
    if 'theme' not in data or data['theme'] not in ['light', 'dark']:
        return jsonify({'error': 'Invalid theme value'}), 400
    
    current_user.set_preference('theme', data['theme'])
    db.session.commit()
    return jsonify({'success': True})

@profile_bp.route('/avatar', methods=['POST'])
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
