"""Icon management routes."""
from flask import jsonify, request
from flask_login import login_required
from app.utils.enhanced_rbac import requires_permission
from app.routes.admin import admin_bp as bp
from app.utils.activity_tracking import track_activity

@bp.route('/icons')
@login_required
@requires_permission('admin_icons_access', 'read')
@track_activity
def get_icons():
    """Get list of available FontAwesome icons with categories."""
    icons = {
        'User Interface': [
            'fa-user', 'fa-users', 'fa-cog', 'fa-wrench', 'fa-gear',
            'fa-dashboard', 'fa-tachometer', 'fa-sliders'
        ],
        'Navigation': [
            'fa-home', 'fa-compass', 'fa-map', 'fa-location-dot',
            'fa-arrow-left', 'fa-arrow-right', 'fa-arrows'
        ],
        'Actions': [
            'fa-plus', 'fa-minus', 'fa-edit', 'fa-trash', 'fa-save',
            'fa-check', 'fa-times', 'fa-refresh', 'fa-sync'
        ],
        'Communication': [
            'fa-envelope', 'fa-bell', 'fa-comment', 'fa-comments',
            'fa-phone', 'fa-video', 'fa-microphone'
        ],
        'Data': [
            'fa-database', 'fa-server', 'fa-cloud', 'fa-file',
            'fa-folder', 'fa-archive', 'fa-box'
        ],
        'Security': [
            'fa-lock', 'fa-unlock', 'fa-shield', 'fa-key',
            'fa-user-shield', 'fa-fingerprint', 'fa-id-card'
        ],
        'Status': [
            'fa-check-circle', 'fa-times-circle', 'fa-exclamation-circle',
            'fa-info-circle', 'fa-question-circle'
        ],
        'Media': [
            'fa-image', 'fa-video', 'fa-music', 'fa-camera',
            'fa-play', 'fa-pause', 'fa-stop'
        ],
        'Business': [
            'fa-chart-line', 'fa-chart-bar', 'fa-chart-pie',
            'fa-dollar-sign', 'fa-euro-sign', 'fa-bitcoin-sign'
        ],
        'Development': [
            'fa-code', 'fa-terminal', 'fa-bug', 'fa-git',
            'fa-github', 'fa-gitlab', 'fa-stack-overflow'
        ],
        'Time': [
            'fa-clock', 'fa-calendar', 'fa-hourglass',
            'fa-stopwatch', 'fa-history'
        ],
        'Social': [
            'fa-twitter', 'fa-facebook', 'fa-linkedin',
            'fa-instagram', 'fa-youtube'
        ]
    }
    
    # Flatten if no category requested
    if not request.args.get('categorized'):
        return jsonify([icon for category in icons.values() for icon in category])
    
    return jsonify(icons)

@bp.route('/icons/search')
@login_required
@requires_permission('admin_icons_access', 'read')
def search_icons():
    """Search for icons by name."""
    query = request.args.get('q', '').lower()
    category = request.args.get('category')
    
    icons = {
        'User Interface': [
            'fa-user', 'fa-users', 'fa-cog', 'fa-wrench', 'fa-gear',
            'fa-dashboard', 'fa-tachometer', 'fa-sliders'
        ],
        'Navigation': [
            'fa-home', 'fa-compass', 'fa-map', 'fa-location-dot',
            'fa-arrow-left', 'fa-arrow-right', 'fa-arrows'
        ],
        'Actions': [
            'fa-plus', 'fa-minus', 'fa-edit', 'fa-trash', 'fa-save',
            'fa-check', 'fa-times', 'fa-refresh', 'fa-sync'
        ],
        'Communication': [
            'fa-envelope', 'fa-bell', 'fa-comment', 'fa-comments',
            'fa-phone', 'fa-video', 'fa-microphone'
        ],
        'Data': [
            'fa-database', 'fa-server', 'fa-cloud', 'fa-file',
            'fa-folder', 'fa-archive', 'fa-box'
        ],
        'Security': [
            'fa-lock', 'fa-unlock', 'fa-shield', 'fa-key',
            'fa-user-shield', 'fa-fingerprint', 'fa-id-card'
        ]
    }
    
    if category and category in icons:
        # Search within specific category
        matches = [icon for icon in icons[category] if query in icon.lower()]
    else:
        # Search all categories
        matches = [
            icon for category_icons in icons.values()
            for icon in category_icons
            if query in icon.lower()
        ]
    
    return jsonify({
        'icons': matches,
        'total': len(matches)
    })

@bp.route('/icons/categories')
@login_required
@requires_permission('admin_icons_access', 'read')
def get_icon_categories():
    """Get list of icon categories."""
    categories = [
        'User Interface',
        'Navigation',
        'Actions',
        'Communication',
        'Data',
        'Security',
        'Status',
        'Media',
        'Business',
        'Development',
        'Time',
        'Social'
    ]
    return jsonify(categories)

@bp.route('/icons/validate')
@login_required
@requires_permission('admin_icons_access', 'read')
def validate_icon():
    """Validate if an icon name is valid."""
    icon = request.args.get('icon', '').strip()
    
    # Basic validation
    if not icon:
        return jsonify({
            'valid': False,
            'message': 'Icon name is required'
        })
    
    if not icon.startswith('fa-'):
        return jsonify({
            'valid': False,
            'message': 'Icon name must start with "fa-"'
        })
    
    # Get all icons
    all_icons = []
    icons = get_icons().get_json()
    if isinstance(icons, dict):
        for category_icons in icons.values():
            all_icons.extend(category_icons)
    else:
        all_icons = icons
    
    # Check if icon exists
    if icon not in all_icons:
        return jsonify({
            'valid': False,
            'message': 'Invalid icon name'
        })
    
    return jsonify({
        'valid': True,
        'message': 'Valid icon name'
    })
