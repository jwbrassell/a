from flask import render_template, request, jsonify, flash, redirect, url_for, current_app, send_file
from flask_login import current_user, login_required
from app.extensions import db, cache
from app.utils.rbac import requires_roles
from .models import WebLink, Tag, WebLinkHistory, weblink_tags
import json
from sqlalchemy import desc, func
from sqlalchemy.exc import OperationalError
import os
import re
from . import bp
import csv
from io import StringIO, BytesIO

@bp.route('/')
@login_required
def index():
    return render_template('weblinks/index.html')

@bp.route('/admin')
@login_required
@requires_roles('admin')
def admin():
    return render_template('weblinks/admin.html')

@bp.route('/admin/stats')
@login_required
@requires_roles('admin')
def get_stats():
    # Get basic stats
    total_links = WebLink.query.count()
    total_clicks = db.session.query(func.sum(WebLink.click_count)).scalar() or 0
    total_tags = Tag.query.count()
    
    # Get popular links
    popular_links = WebLink.query.order_by(desc(WebLink.click_count)).limit(10).all()
    
    # Get tags distribution
    tags_distribution = db.session.query(
        Tag,
        func.count(weblink_tags.c.weblink_id).label('count')
    ).join(
        weblink_tags
    ).group_by(
        Tag
    ).all()
    
    return jsonify({
        'total_links': total_links,
        'total_clicks': total_clicks,
        'total_tags': total_tags,
        'popular_links': [{
            'title': link.title,
            'clicks': link.click_count
        } for link in popular_links],
        'tags_distribution': [{
            'name': tag.name,
            'count': count
        } for tag, count in tags_distribution]
    })

@bp.route('/admin/template')
@login_required
@requires_roles('admin')
def download_template():
    # Create CSV template
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['url', 'title', 'description', 'icon', 'tags'])
    writer.writerow(['https://example.com', 'Example Title', 'Description here', 'fas fa-link', 'tag1,tag2'])
    
    # Convert to bytes for send_file
    bytes_output = BytesIO()
    bytes_output.write(output.getvalue().encode('utf-8'))
    bytes_output.seek(0)
    
    return send_file(
        bytes_output,
        mimetype='text/csv',
        as_attachment=True,
        download_name='weblinks_template.csv'
    )

@bp.route('/admin/bulk-upload', methods=['POST'])
@login_required
@requires_roles('admin')
def bulk_upload():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'})
    
    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return jsonify({'success': False, 'error': 'File must be CSV'})
    
    try:
        # Read CSV file
        stream = StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)
        
        for row in csv_reader:
            # Check for required fields
            if not row.get('url') or not row.get('title'):
                continue
                
            # Create or update link
            link = WebLink.query.filter_by(url=row['url']).first()
            if not link:
                link = WebLink(
                    url=row['url'],
                    title=row['title'],
                    description=row.get('description', ''),
                    icon=row.get('icon', 'fas fa-link'),
                    created_by=current_user.id
                )
                db.session.add(link)
            
            # Handle tags
            if row.get('tags'):
                tags = [t.strip() for t in row['tags'].split(',')]
                for tag_name in tags:
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.session.add(tag)
                    if tag not in link.tags:
                        link.tags.append(tag)
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/admin/bulk-tags', methods=['POST'])
@login_required
@requires_roles('admin')
def bulk_tags():
    data = request.json
    if not data or 'tags' not in data:
        return jsonify({'success': False, 'error': 'No tags provided'})
    
    try:
        for tag_name in data['tags']:
            if not Tag.query.filter_by(name=tag_name).first():
                tag = Tag(name=tag_name)
                db.session.add(tag)
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

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
