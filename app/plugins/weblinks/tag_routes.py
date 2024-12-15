"""Tag management routes for Weblinks plugin."""

from datetime import datetime
from flask import jsonify, request
from flask_login import login_required, current_user
from app import db
from app.utils.enhanced_rbac import requires_permission
from .models import WebLinkTag

def register_routes(bp):
    """Register tag management routes with blueprint."""

    @bp.route('/api/tags')
    @login_required
    @requires_permission('weblinks_access', 'read')
    def get_tags():
        """Get all tags."""
        tags = WebLinkTag.query.filter_by(deleted_at=None).all()
        return jsonify([tag.to_dict() for tag in tags])

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
            existing = WebLinkTag.query.filter_by(
                name=name,
                deleted_at=None
            ).first()
            if existing:
                return jsonify({
                    'success': True,
                    'id': existing.id,
                    'name': existing.name
                })

            # Create new tag
            tag = WebLinkTag(
                name=name,
                created_by=current_user.id,
                updated_by=current_user.id
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

    @bp.route('/tag/<int:tag_id>/edit', methods=['PUT'])
    @login_required
    @requires_permission('weblinks_manage', 'write')
    def edit_tag(tag_id):
        """Edit an existing tag."""
        tag = WebLinkTag.query.filter_by(
            id=tag_id,
            deleted_at=None
        ).first_or_404()

        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({
                'success': False,
                'error': 'Name is required'
            }), 400

        try:
            # Check for existing tag with same name
            existing = WebLinkTag.query.filter_by(
                name=data['name'],
                deleted_at=None
            ).first()
            if existing and existing.id != tag_id:
                return jsonify({
                    'success': False,
                    'error': 'Tag name already exists'
                }), 400

            tag.name = data['name']
            tag.updated_by = current_user.id
            tag.updated_at = datetime.utcnow()
            db.session.commit()

            return jsonify({
                'success': True,
                'tag': tag.to_dict()
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/tag/<int:tag_id>', methods=['DELETE'])
    @login_required
    @requires_permission('weblinks_manage', 'write')
    def delete_tag(tag_id):
        """Soft delete a tag."""
        tag = WebLinkTag.query.filter_by(
            id=tag_id,
            deleted_at=None
        ).first_or_404()

        try:
            # Check if tag has active links
            active_links = [link for link in tag.links if link.deleted_at is None]
            if active_links:
                return jsonify({
                    'success': False,
                    'error': 'Cannot delete tag with active links'
                }), 400

            tag.deleted_at = datetime.utcnow()
            tag.updated_by = current_user.id
            tag.updated_at = datetime.utcnow()
            db.session.commit()

            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/api/tag/<int:tag_id>/stats')
    @login_required
    @requires_permission('weblinks_access', 'read')
    def get_tag_stats(tag_id):
        """Get statistics for a specific tag."""
        tag = WebLinkTag.query.filter_by(
            id=tag_id,
            deleted_at=None
        ).first_or_404()

        active_links = [link for link in tag.links if link.deleted_at is None]
        categories = {}
        for link in active_links:
            if link.category:
                category_name = link.category.name
                categories[category_name] = categories.get(category_name, 0) + 1

        return jsonify({
            'total_links': len(active_links),
            'categories': [
                {'name': name, 'count': count}
                for name, count in categories.items()
            ],
            'related_tags': [
                {
                    'name': related_tag.name,
                    'count': len([
                        link for link in related_tag.links 
                        if link.deleted_at is None and tag in link.tags
                    ])
                }
                for related_tag in WebLinkTag.query.filter(
                    WebLinkTag.id != tag_id,
                    WebLinkTag.deleted_at.is_(None)
                ).all()
                if any(link for link in related_tag.links 
                      if link.deleted_at is None and tag in link.tags)
            ]
        })
