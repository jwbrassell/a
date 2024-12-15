from flask import render_template, flash, redirect, url_for, request, jsonify, send_file, make_response
from flask_login import login_required, current_user
from sqlalchemy import or_, func
from app import db
from app.plugins.weblinks import bp
from app.plugins.weblinks.models import WebLink, WebLinkCategory, WebLinkTag, weblink_tag_association
from app.plugins.weblinks.forms import WebLinkForm, CategoryForm, TagForm
from app.utils.enhanced_rbac import requires_permission
import csv
from io import StringIO
import tempfile
from datetime import datetime

@bp.route('/')
@login_required
@requires_permission('weblinks_access', 'read')
def index():
    """Display main web links page."""
    categories = WebLinkCategory.query.all()
    tags = WebLinkTag.query.all()
    return render_template('weblinks/index.html',
                         categories=categories,
                         tags=tags)

@bp.route('/api/links')
@login_required
@requires_permission('weblinks_access', 'read')
def get_links():
    """Get all links for DataTables."""
    links = WebLink.query.all()
    return jsonify({'data': [link.to_dict() for link in links]})

@bp.route('/link/add', methods=['GET', 'POST'])
@login_required
@requires_permission('weblinks_manage', 'write')
def add_link():
    """Add a new web link."""
    form = WebLinkForm()
    tags = WebLinkTag.query.all()
    
    # Populate category and tag choices
    form.category.choices = [(c.id, c.name) for c in WebLinkCategory.query.all()]
    form.tags.choices = [(t.id, t.name) for t in WebLinkTag.query.all()]
    
    if form.validate_on_submit():
        try:
            # Check for duplicate URL
            if WebLink.query.filter_by(url=form.url.data).first():
                flash('URL already exists!', 'error')
                return redirect(url_for('weblinks.add_link'))
            
            link = WebLink(
                url=form.url.data,
                friendly_name=form.friendly_name.data,
                notes=form.notes.data,
                icon=form.icon.data,
                category_id=form.category.data,
                created_by=current_user.username
            )
            
            # Add selected tags
            if form.tags.data:
                selected_tags = WebLinkTag.query.filter(WebLinkTag.id.in_(form.tags.data)).all()
                link.tags.extend(selected_tags)
            
            db.session.add(link)
            db.session.commit()
            flash('Link added successfully!', 'success')
            return redirect(url_for('weblinks.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding link: {str(e)}', 'error')
    
    return render_template('weblinks/add_link.html', form=form, tags=tags)

@bp.route('/api/stats')
@login_required
@requires_permission('weblinks_access', 'read')
def get_stats():
    """Get statistics for charts."""
    try:
        # Get category stats
        category_stats = db.session.query(
            WebLinkCategory.name,
            func.count(WebLink.id)
        ).outerjoin(WebLink).group_by(WebLinkCategory.name).all()
        
        # Get tag stats using subquery for accurate counts
        tag_stats = db.session.query(
            WebLinkTag.name,
            func.count(WebLink.id)
        ).outerjoin(
            weblink_tag_association,
            WebLinkTag.id == weblink_tag_association.c.tag_id
        ).outerjoin(
            WebLink,
            WebLink.id == weblink_tag_association.c.weblink_id
        ).group_by(WebLinkTag.name).all()
        
        return jsonify({
            'categories': [{'name': name or 'Uncategorized', 'count': count} for name, count in category_stats],
            'tags': [{'name': name, 'count': count} for name, count in tag_stats]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/category/add', methods=['POST'])
@login_required
@requires_permission('weblinks_manage', 'write')
def add_category():
    """Add a new category."""
    form = CategoryForm()
    if form.validate_on_submit():
        try:
            category = WebLinkCategory(
                name=form.name.data,
                created_by=current_user.username
            )
            db.session.add(category)
            db.session.commit()
            return jsonify({
                'success': True,
                'id': category.id,
                'name': category.name
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    return jsonify({
        'success': False,
        'errors': form.errors
    }), 400

@bp.route('/tag/add', methods=['POST'])
@login_required
@requires_permission('weblinks_manage', 'write')
def add_tag():
    """Add a new tag."""
    name = request.form.get('name')
    if not name:
        return jsonify({
            'success': False,
            'error': 'Tag name is required'
        }), 400

    try:
        # Check if tag already exists
        tag = WebLinkTag.query.filter_by(name=name).first()
        if tag:
            return jsonify({
                'success': True,
                'id': tag.id,
                'name': tag.name
            })

        # Create new tag
        tag = WebLinkTag(
            name=name,
            created_by=current_user.username
        )
        db.session.add(tag)
        db.session.commit()
        return jsonify({
            'success': True,
            'id': tag.id,
            'name': tag.name
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/icons')
@login_required
@requires_permission('weblinks_access', 'read')
def get_icons():
    """Get list of Font Awesome icons."""
    icons = [
        'fa-link', 'fa-globe', 'fa-bookmark', 'fa-star', 'fa-heart',
        'fa-file', 'fa-book', 'fa-code', 'fa-database', 'fa-cloud',
        'fa-server', 'fa-laptop', 'fa-desktop', 'fa-mobile', 'fa-tablet',
        'fa-envelope', 'fa-paper-plane', 'fa-comment', 'fa-chat',
        'fa-github', 'fa-gitlab', 'fa-bitbucket', 'fa-jira',
        'fa-confluence', 'fa-slack', 'fa-trello', 'fa-asana'
    ]
    return jsonify(icons)

@bp.route('/export/csv')
@login_required
@requires_permission('weblinks_import_export', 'read')
def export_csv():
    """Export links to CSV."""
    try:
        links = WebLink.query.all()
        
        # Create CSV in memory
        si = StringIO()
        writer = csv.writer(si)
        
        # Write header
        writer.writerow(['URL', 'Friendly Name', 'Category', 'Tags', 'Notes', 'Icon'])
        
        # Write data
        for link in links:
            writer.writerow([
                link.url,
                link.friendly_name,
                link.category.name if link.category else '',
                ','.join(tag.name for tag in link.tags),
                link.notes or '',
                link.icon or ''
            ])
        
        # Create response
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = f"attachment; filename=weblinks_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        output.headers["Content-type"] = "text/csv"
        return output
        
    except Exception as e:
        flash(f'Error exporting CSV: {str(e)}', 'error')
        return redirect(url_for('weblinks.index'))

@bp.route('/import/csv', methods=['POST'])
@login_required
@requires_permission('weblinks_import_export', 'write')
def import_csv():
    """Import links from CSV."""
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'error': 'No file uploaded'
        }), 400
    
    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return jsonify({
            'success': False,
            'error': 'File must be a CSV'
        }), 400
    
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
            file.save(temp_file.name)
            temp_file.seek(0)
            reader = csv.DictReader(temp_file)
            
            for row in reader:
                # Get or create category
                category = None
                if row.get('Category'):
                    category = WebLinkCategory.query.filter_by(name=row['Category']).first()
                    if not category:
                        category = WebLinkCategory(
                            name=row['Category'],
                            created_by=current_user.username
                        )
                        db.session.add(category)
                
                # Create link
                link = WebLink(
                    url=row['URL'],
                    friendly_name=row['Friendly Name'],
                    notes=row.get('Notes', ''),
                    icon=row.get('Icon', ''),
                    category=category,
                    created_by=current_user.username
                )
                
                # Handle tags
                if row.get('Tags'):
                    tag_names = [t.strip() for t in row['Tags'].split(',')]
                    for tag_name in tag_names:
                        tag = WebLinkTag.query.filter_by(name=tag_name).first()
                        if not tag:
                            tag = WebLinkTag(
                                name=tag_name,
                                created_by=current_user.username
                            )
                            db.session.add(tag)
                        link.tags.append(tag)
                
                db.session.add(link)
            
            db.session.commit()
            
        return jsonify({
            'success': True
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/search')
@login_required
@requires_permission('weblinks_access', 'read')
def search():
    """Search web links."""
    query = request.args.get('q', '')
    category_id = request.args.get('category', type=int)
    tag_id = request.args.get('tag', type=int)
    
    links = WebLink.query
    
    if query:
        links = links.filter(
            or_(
                WebLink.friendly_name.ilike(f'%{query}%'),
                WebLink.url.ilike(f'%{query}%'),
                WebLink.notes.ilike(f'%{query}%')
            )
        )
    
    if category_id:
        links = links.filter_by(category_id=category_id)
    
    if tag_id:
        links = links.filter(WebLink.tags.any(id=tag_id))
    
    links = links.order_by(WebLink.created_at.desc()).all()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify([link.to_dict() for link in links])
    
    return jsonify([link.to_dict() for link in links])
