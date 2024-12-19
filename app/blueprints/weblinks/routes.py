from flask import render_template, request, jsonify, flash, redirect, url_for, current_app
from flask_login import current_user, login_required
from app.extensions import db, cache
from app.utils.rbac import requires_roles
from .models import WebLink, Tag, WebLinkHistory
import json
from sqlalchemy import desc
from sqlalchemy.exc import OperationalError
import os
import re
from . import bp

@bp.route('/')
@login_required
def index():
    return render_template('weblinks/index.html')

@bp.route('/get_links')
@login_required
def get_links():
    try:
        links = WebLink.query.all()
        return jsonify([{
            'id': link.id,
            'url': link.url,
            'title': link.title,
            'description': link.description,
            'icon': link.icon,
            'tags': [tag.name for tag in link.tags],
            'created_by': link.creator.username if link.creator else None,
            'created_at': link.created_at.isoformat(),
            'updated_at': link.updated_at.isoformat()
        } for link in links])
    except OperationalError:
        return jsonify([])

@bp.route('/get_common_links')
@login_required
def get_common_links():
    try:
        # Get top 10 most clicked links
        common_links = WebLink.query.order_by(desc(WebLink.click_count)).limit(10).all()
        
        # Keep track of URLs we've already added to prevent duplicates
        added_urls = {link.url for link in common_links}
        result_links = list(common_links)
        
        # If we need more links, get recent ones that aren't already included
        if len(result_links) < 10:
            recent_links = WebLink.query.filter(~WebLink.url.in_(added_urls))\
                .order_by(desc(WebLink.created_at))\
                .limit(10-len(result_links)).all()
            result_links.extend(recent_links)
        
        return jsonify([{
            'id': link.id,
            'url': link.url,
            'title': link.title,
            'icon': link.icon
        } for link in result_links])
    except OperationalError:
        return jsonify([])

@bp.route('/get_link/<int:link_id>')
@login_required
def get_link(link_id):
    try:
        link = WebLink.query.get_or_404(link_id)
        history = [{
            'changed_by': entry.editor.username,
            'changed_at': entry.changed_at.isoformat(),
            'changes': entry.changes
        } for entry in link.history.order_by(desc(WebLinkHistory.changed_at)).all()]
        
        return jsonify({
            'id': link.id,
            'url': link.url,
            'title': link.title,
            'description': link.description,
            'icon': link.icon,
            'tags': [tag.name for tag in link.tags],
            'created_by': link.creator.username if link.creator else None,
            'created_at': link.created_at.isoformat(),
            'history': history
        })
    except OperationalError:
        return jsonify({'error': 'Database not initialized'}), 500

@bp.route('/create_link', methods=['POST'])
@login_required
@requires_roles('edit_links')
def create_link():
    try:
        data = request.json
        
        # Check for duplicate URL
        if WebLink.query.filter_by(url=data['url']).first():
            return jsonify({'error': 'URL already exists'}), 400
        
        link = WebLink(
            url=data['url'],
            title=data['title'],
            description=data.get('description', ''),
            icon=data.get('icon', 'fas fa-link'),
            created_by=current_user.id
        )
        
        # Handle tags
        for tag_name in data.get('tags', []):
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.session.add(tag)
            link.tags.append(tag)
        
        db.session.add(link)
        db.session.commit()
        
        return jsonify({'id': link.id}), 201
    except OperationalError:
        return jsonify({'error': 'Database not initialized'}), 500

@bp.route('/update_link/<int:link_id>', methods=['PUT'])
@login_required
@requires_roles('edit_links')
def update_link(link_id):
    try:
        link = WebLink.query.get_or_404(link_id)
        data = request.json
        changes = {}
        
        # Track changes
        if data.get('url') and data['url'] != link.url:
            changes['url'] = {'old': link.url, 'new': data['url']}
            link.url = data['url']
        
        if data.get('title') and data['title'] != link.title:
            changes['title'] = {'old': link.title, 'new': data['title']}
            link.title = data['title']
        
        if 'description' in data and data['description'] != link.description:
            changes['description'] = {'old': link.description, 'new': data['description']}
            link.description = data['description']
        
        if data.get('icon') and data['icon'] != link.icon:
            changes['icon'] = {'old': link.icon, 'new': data['icon']}
            link.icon = data['icon']
        
        # Handle tags
        if 'tags' in data:
            old_tags = set(tag.name for tag in link.tags)
            new_tags = set(data['tags'])
            if old_tags != new_tags:
                changes['tags'] = {'old': list(old_tags), 'new': list(new_tags)}
                link.tags = []
                for tag_name in new_tags:
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.session.add(tag)
                    link.tags.append(tag)
        
        if changes:
            history = WebLinkHistory(
                weblink_id=link.id,
                changed_by=current_user.id,
                changes=changes
            )
            db.session.add(history)
        
        db.session.commit()
        return jsonify({'success': True})
    except OperationalError:
        return jsonify({'error': 'Database not initialized'}), 500

@bp.route('/record_click/<int:link_id>', methods=['POST'])
@login_required
def record_click(link_id):
    try:
        link = WebLink.query.get_or_404(link_id)
        link.click_count += 1
        db.session.commit()
        return jsonify({'success': True})
    except OperationalError:
        return jsonify({'error': 'Database not initialized'}), 500

@bp.route('/get_tags')
@login_required
def get_tags():
    try:
        tags = Tag.query.all()
        return jsonify([{
            'id': tag.id,
            'name': tag.name
        } for tag in tags])
    except OperationalError:
        return jsonify([])

@cache.cached(timeout=3600, key_prefix='fontawesome_icons')
def get_cached_fontawesome_icons():
    # Load icons from Font Awesome CSS file
    icons = []
    try:
        with open(os.path.join(current_app.static_folder, 'fontawesome/css/all.css'), 'r') as f:
            content = f.read()
            # Find all .fa-* class definitions
            matches = re.findall(r'\.fa-([a-z0-9-]+):before', content)
            icons = ['fas fa-' + match for match in matches]
    except:
        # Fallback to basic icons if file not found
        icons = [
            'fas fa-link', 'fas fa-globe', 'fas fa-book', 'fas fa-file',
            'fas fa-code', 'fas fa-database', 'fas fa-server', 'fas fa-cloud',
            'fas fa-cog', 'fas fa-users', 'fas fa-folder', 'fas fa-search',
            'fas fa-star', 'fas fa-heart', 'fas fa-home', 'fas fa-clock',
            'fas fa-calendar', 'fas fa-chart-bar', 'fas fa-envelope',
            'fas fa-phone'
        ]
    return icons

@bp.route('/search_icons')
@login_required
def search_icons():
    query = request.args.get('q', '').lower()
    page = int(request.args.get('page', 1))
    per_page = 20
    
    all_icons = get_cached_fontawesome_icons()
    
    if query:
        filtered_icons = [icon for icon in all_icons if query in icon.lower()]
    else:
        filtered_icons = all_icons
    
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    return jsonify({
        'icons': filtered_icons[start_idx:end_idx],
        'has_more': end_idx < len(filtered_icons)
    })

@bp.route('/get_icons')
@login_required
def get_icons():
    icons = get_cached_fontawesome_icons()
    return jsonify(icons)
