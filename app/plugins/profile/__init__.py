"""User profile management plugin."""

from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify
from flask_login import login_required, current_user
import os
from werkzeug.utils import secure_filename
import random
from datetime import datetime
from app import db
from app.utils.plugin_manager import PluginMetadata
from app.utils.activity_tracking import track_activity
from app.models import UserActivity

# Create blueprint
bp = Blueprint('profile', __name__, 
              template_folder='templates',
              static_folder='static',
              url_prefix='/profile')

# Define plugin metadata
plugin_metadata = PluginMetadata(
    name="Profile",
    version="1.0.0",
    description="User profile management including avatar and theme preferences",
    author="Portal Team",
    required_roles=[],  # No specific roles required - available to all authenticated users
    icon="fa-user",
    category="",  # No category - will appear in uncategorized
    weight=100
)

# Constants
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
DEFAULT_AVATARS = [
    '8bitsq.jpg', 'bary.jpg', 'blackhole.jpg', 'solarsystem.jpg',
    'stego.jpg', 'synthsq.jpg', 'user_1.jpg', 'veloci.jpg'
]

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/', methods=['GET', 'POST'])
@login_required
@track_activity
def index():
    if request.method == 'POST':
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file.filename == '':
                flash('No file selected', 'error')
                return redirect(request.url)
            
            if file and allowed_file(file.filename):
                # Check file size (1MB limit)
                file_data = file.read()
                if len(file_data) > 1 * 1024 * 1024:  # 1MB in bytes
                    flash('File size must be less than 1MB', 'error')
                    return redirect(request.url)
                
                filename = secure_filename(file.filename)
                # Create unique filename using user ID and timestamp
                ext = filename.rsplit('.', 1)[1].lower()
                new_filename = f"avatar_{current_user.id}_{int(datetime.now().timestamp())}.{ext}"
                
                # Save file
                upload_path = os.path.join(current_app.root_path, 'static', 'uploads', 'avatars')
                os.makedirs(upload_path, exist_ok=True)
                file_path = os.path.join(upload_path, new_filename)
                
                with open(file_path, 'wb') as f:
                    f.write(file_data)
                
                # Update user preferences
                current_user.set_preference('avatar', f'uploads/avatars/{new_filename}')
                flash('Avatar uploaded successfully', 'success')
                return redirect(url_for('profile.index'))
            else:
                flash('Invalid file type. Only PNG and JPG files are allowed.', 'error')
                return redirect(request.url)
        
        elif 'default_avatar' in request.form:
            avatar = request.form['default_avatar']
            if avatar in DEFAULT_AVATARS:
                current_user.set_preference('avatar', f'images/{avatar}')
                flash('Avatar updated successfully', 'success')
            return redirect(url_for('profile.index'))
        
        elif 'theme' in request.form:
            theme = request.form['theme']
            if theme in ['light', 'dark']:
                current_user.set_preference('theme', theme)
                flash('Theme preference updated', 'success')
            return redirect(url_for('profile.index'))

    # Get current preferences
    theme = current_user.get_preference('theme', 'light')
    avatar = current_user.get_preference('avatar')
    
    # If no avatar is set, assign a random default
    if not avatar:
        avatar = f'images/{random.choice(DEFAULT_AVATARS)}'
        current_user.set_preference('avatar', avatar)

    # Get user activities
    activities = UserActivity.query.filter_by(user_id=current_user.id)\
        .order_by(UserActivity.timestamp.desc())\
        .all()

    return render_template('profile/index.html', 
                         theme=theme,
                         avatar=avatar,
                         default_avatars=DEFAULT_AVATARS,
                         activities=activities)

@bp.route('/preferences/theme', methods=['POST'])
@login_required
def update_theme():
    """API endpoint for updating theme preference via AJAX"""
    data = request.get_json()
    theme = data.get('theme')
    
    if theme not in ['light', 'dark']:
        return jsonify({'error': 'Invalid theme'}), 400
        
    current_user.set_preference('theme', theme)
    return jsonify({'status': 'success'})

# Create uploads directory on blueprint registration
@bp.record_once
def init_uploads(state):
    upload_path = os.path.join(state.app.root_path, 'static', 'uploads', 'avatars')
    os.makedirs(upload_path, exist_ok=True)
