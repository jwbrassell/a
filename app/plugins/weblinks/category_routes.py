"""Category management routes for Weblinks plugin."""

from datetime import datetime
from flask import jsonify, request
from flask_login import login_required, current_user
from app import db
from app.utils.enhanced_rbac import requires_permission
from .models import WebLinkCategory
from .forms import CategoryForm

def register_routes(bp):
    """Register category management routes with blueprint."""

    @bp.route('/api/categories')
    @login_required
    @requires_permission('weblinks_access', 'read')
    def get_categories():
        """Get all categories."""
        categories = WebLinkCategory.query.filter_by(deleted_at=None).all()
        return jsonify([category.to_dict() for category in categories])

    @bp.route('/category/add', methods=['POST'])
    @login_required
    @requires_permission('weblinks_manage', 'write')
    def add_category():
        """Add a new category."""
        form = CategoryForm()
        if form.validate_on_submit():
            try:
                # Check for existing category
                existing = WebLinkCategory.query.filter_by(
                    name=form.name.data,
                    deleted_at=None
                ).first()
                if existing:
                    return jsonify({
                        'success': False,
                        'error': 'Category already exists'
                    }), 400

                category = WebLinkCategory(
                    name=form.name.data,
                    created_by=current_user.id,
                    updated_by=current_user.id
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

    @bp.route('/category/<int:category_id>/edit', methods=['PUT'])
    @login_required
    @requires_permission('weblinks_manage', 'write')
    def edit_category(category_id):
        """Edit an existing category."""
        category = WebLinkCategory.query.filter_by(
            id=category_id,
            deleted_at=None
        ).first_or_404()

        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({
                'success': False,
                'error': 'Name is required'
            }), 400

        try:
            # Check for existing category with same name
            existing = WebLinkCategory.query.filter_by(
                name=data['name'],
                deleted_at=None
            ).first()
            if existing and existing.id != category_id:
                return jsonify({
                    'success': False,
                    'error': 'Category name already exists'
                }), 400

            category.name = data['name']
            category.updated_by = current_user.id
            category.updated_at = datetime.utcnow()
            db.session.commit()

            return jsonify({
                'success': True,
                'category': category.to_dict()
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/category/<int:category_id>', methods=['DELETE'])
    @login_required
    @requires_permission('weblinks_manage', 'write')
    def delete_category(category_id):
        """Soft delete a category."""
        category = WebLinkCategory.query.filter_by(
            id=category_id,
            deleted_at=None
        ).first_or_404()

        try:
            # Check if category has active links
            active_links = [link for link in category.links if link.deleted_at is None]
            if active_links:
                return jsonify({
                    'success': False,
                    'error': 'Cannot delete category with active links'
                }), 400

            category.deleted_at = datetime.utcnow()
            category.updated_by = current_user.id
            category.updated_at = datetime.utcnow()
            db.session.commit()

            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/api/category/<int:category_id>/stats')
    @login_required
    @requires_permission('weblinks_access', 'read')
    def get_category_stats(category_id):
        """Get statistics for a specific category."""
        category = WebLinkCategory.query.filter_by(
            id=category_id,
            deleted_at=None
        ).first_or_404()

        active_links = [link for link in category.links if link.deleted_at is None]
        return jsonify({
            'total_links': len(active_links),
            'tags': [
                {
                    'name': tag.name,
                    'count': len([
                        link for link in tag.links 
                        if link.category_id == category_id and link.deleted_at is None
                    ])
                }
                for tag in set(tag for link in active_links for tag in link.tags)
            ]
        })
