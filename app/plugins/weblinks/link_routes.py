"""Link management routes for Weblinks plugin."""

from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_
from app import db
from app.utils.enhanced_rbac import requires_permission
from .models import WebLink, WebLinkCategory, WebLinkTag
from .forms import WebLinkForm

def register_routes(bp):
    """Register link management routes with blueprint."""

    @bp.route('/')
    @login_required
    @requires_permission('weblinks_access', 'read')
    def index():
        """Display main web links page."""
        categories = WebLinkCategory.query.filter_by(deleted_at=None).all()
        tags = WebLinkTag.query.filter_by(deleted_at=None).all()
        return render_template('weblinks/index.html',
                            categories=categories,
                            tags=tags)

    @bp.route('/api/links')
    @login_required
    @requires_permission('weblinks_access', 'read')
    def get_links():
        """Get all links for DataTables."""
        links = WebLink.query.filter_by(deleted_at=None).all()
        return jsonify({'data': [link.to_dict() for link in links]})

    @bp.route('/link/add', methods=['GET', 'POST'])
    @login_required
    @requires_permission('weblinks_manage', 'write')
    def add_link():
        """Add a new web link."""
        form = WebLinkForm()
        tags = WebLinkTag.query.filter_by(deleted_at=None).all()
        
        # Populate category and tag choices
        form.category.choices = [(c.id, c.name) for c in WebLinkCategory.query.filter_by(deleted_at=None).all()]
        form.tags.choices = [(t.id, t.name) for t in tags]
        
        if form.validate_on_submit():
            try:
                # Check for duplicate URL
                if WebLink.query.filter_by(url=form.url.data, deleted_at=None).first():
                    flash('URL already exists!', 'error')
                    return redirect(url_for('weblinks.add_link'))
                
                link = WebLink(
                    url=form.url.data,
                    friendly_name=form.friendly_name.data,
                    notes=form.notes.data,
                    icon=form.icon.data,
                    category_id=form.category.data,
                    created_by=current_user.id,
                    updated_by=current_user.id
                )
                
                # Add selected tags
                if form.tags.data:
                    selected_tags = WebLinkTag.query.filter(
                        WebLinkTag.id.in_(form.tags.data),
                        WebLinkTag.deleted_at.is_(None)
                    ).all()
                    link.tags.extend(selected_tags)
                
                db.session.add(link)
                db.session.commit()
                flash('Link added successfully!', 'success')
                return redirect(url_for('weblinks.index'))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Error adding link: {str(e)}', 'error')
        
        return render_template('weblinks/add_link.html', form=form, tags=tags)

    @bp.route('/link/<int:link_id>/edit', methods=['GET', 'POST'])
    @login_required
    @requires_permission('weblinks_manage', 'write')
    def edit_link(link_id):
        """Edit an existing web link."""
        link = WebLink.query.filter_by(id=link_id, deleted_at=None).first_or_404()
        form = WebLinkForm(obj=link)
        
        # Populate category and tag choices
        form.category.choices = [(c.id, c.name) for c in WebLinkCategory.query.filter_by(deleted_at=None).all()]
        form.tags.choices = [(t.id, t.name) for t in WebLinkTag.query.filter_by(deleted_at=None).all()]
        
        if form.validate_on_submit():
            try:
                # Check for duplicate URL if changed
                if form.url.data != link.url:
                    existing = WebLink.query.filter_by(url=form.url.data, deleted_at=None).first()
                    if existing and existing.id != link_id:
                        flash('URL already exists!', 'error')
                        return redirect(url_for('weblinks.edit_link', link_id=link_id))
                
                link.url = form.url.data
                link.friendly_name = form.friendly_name.data
                link.notes = form.notes.data
                link.icon = form.icon.data
                link.category_id = form.category.data
                link.updated_by = current_user.id
                link.updated_at = datetime.utcnow()
                
                # Update tags
                link.tags = []
                if form.tags.data:
                    selected_tags = WebLinkTag.query.filter(
                        WebLinkTag.id.in_(form.tags.data),
                        WebLinkTag.deleted_at.is_(None)
                    ).all()
                    link.tags.extend(selected_tags)
                
                db.session.commit()
                flash('Link updated successfully!', 'success')
                return redirect(url_for('weblinks.index'))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating link: {str(e)}', 'error')
        
        return render_template('weblinks/edit_link.html', form=form, link=link)

    @bp.route('/link/<int:link_id>/delete', methods=['POST'])
    @login_required
    @requires_permission('weblinks_manage', 'write')
    def delete_link(link_id):
        """Soft delete a web link."""
        link = WebLink.query.filter_by(id=link_id, deleted_at=None).first_or_404()
        try:
            link.deleted_at = datetime.utcnow()
            link.updated_by = current_user.id
            link.updated_at = datetime.utcnow()
            db.session.commit()
            flash('Link deleted successfully!', 'success')
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500

    @bp.route('/search')
    @login_required
    @requires_permission('weblinks_access', 'read')
    def search():
        """Search web links."""
        query = request.args.get('q', '')
        category_id = request.args.get('category', type=int)
        tag_id = request.args.get('tag', type=int)
        
        links = WebLink.query.filter_by(deleted_at=None)
        
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
