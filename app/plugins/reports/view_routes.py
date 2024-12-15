"""Report view management routes for Reports plugin."""

from datetime import datetime
from flask import jsonify, request, render_template, current_app, abort, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import or_
from app import db
from app.utils.enhanced_rbac import requires_permission
from .models import ReportView, DatabaseConnection, Role

def register_routes(bp):
    """Register view management routes with blueprint."""
    
    @bp.route('/')
    @login_required
    @requires_permission('reports_access', 'read')
    def index():
        """Display the reports dashboard with available views."""
        views = db.session.query(ReportView).filter(
            ReportView.deleted_at.is_(None),
            or_(
                ReportView.created_by == current_user.id,
                ReportView.is_private.is_(False)
            )
        ).all()
        return render_template('reports/dashboard.html', views=views)

    @bp.route('/view/new', methods=['GET', 'POST'])
    @login_required
    @requires_permission('reports_create', 'write')
    def create_view():
        """Create a new report view."""
        if request.method == 'POST':
            data = request.json
            view = ReportView(
                title=data['title'],
                description=data.get('description', ''),
                database_id=data['database_id'],
                query=data['query'],
                column_config=data['column_config'],
                is_private=data.get('is_private', False),
                created_by=current_user.id,
                updated_by=current_user.id
            )
            
            # Add role permissions if specified
            if 'roles' in data:
                roles = Role.query.filter(Role.id.in_(data['roles'])).all()
                view.roles = roles

            db.session.add(view)
            db.session.commit()
            
            flash('Report created successfully', 'success')
            return jsonify({'redirect': url_for('reports.view_report', view_id=view.id)})

        databases = DatabaseConnection.query.filter_by(
            is_active=True,
            deleted_at=None
        ).all()
        return render_template('reports/create_view.html', databases=databases)

    @bp.route('/view/<int:view_id>/edit', methods=['GET', 'POST'])
    @login_required
    @requires_permission('reports_edit', 'write')
    def edit_view(view_id):
        """Edit an existing report view."""
        view = db.session.query(ReportView).filter_by(
            id=view_id,
            deleted_at=None
        ).first()
        if not view:
            abort(404)
        
        # Check permissions
        if view.created_by != current_user.id and not current_user.has_role('admin'):
            abort(403)

        if request.method == 'POST':
            data = request.json
            view.title = data['title']
            view.description = data.get('description', '')
            view.database_id = data['database_id']
            view.query = data['query']
            view.column_config = data['column_config']
            view.is_private = data.get('is_private', False)
            view.updated_by = current_user.id
            view.updated_at = datetime.utcnow()

            # Update role permissions if specified
            if 'roles' in data:
                roles = Role.query.filter(Role.id.in_(data['roles'])).all()
                view.roles = roles

            db.session.commit()
            return jsonify(view.to_dict())

        databases = DatabaseConnection.query.filter_by(
            is_active=True,
            deleted_at=None
        ).all()
        return render_template('reports/edit_view.html', view=view, databases=databases)

    @bp.route('/view/<int:view_id>')
    @login_required
    @requires_permission('reports_access', 'read')
    def view_report(view_id):
        """Display a specific report view."""
        view = db.session.query(ReportView).filter_by(
            id=view_id,
            deleted_at=None
        ).first()
        if not view:
            abort(404)
        
        # Check permissions
        if view.is_private and view.created_by != current_user.id:
            if not any(role in view.roles for role in current_user.roles):
                return jsonify({'error': 'Access denied'}), 403
        
        # Verify database connection exists and is active
        if not view.database or not view.database.is_active or view.database.deleted_at:
            return render_template('reports/view.html', view=view, error="Database connection not found or inactive")
        
        return render_template('reports/view.html', view=view)

    @bp.route('/api/view/<int:view_id>', methods=['DELETE'])
    @login_required
    @requires_permission('reports_delete', 'write')
    def delete_view(view_id):
        """Soft delete a report view."""
        try:
            view = db.session.query(ReportView).filter_by(
                id=view_id,
                deleted_at=None
            ).first()
            if not view:
                return jsonify({'error': 'Report view not found'}), 404
            
            # Check permissions
            if view.created_by != current_user.id and not current_user.has_role('admin'):
                return jsonify({'error': 'Access denied'}), 403
            
            # Clear role associations first
            view.roles = []
            
            # Soft delete the view
            view.deleted_at = datetime.utcnow()
            view.updated_by = current_user.id
            view.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            return '', 204
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error deleting view {view_id}: {str(e)}")
            return jsonify({'error': 'Failed to delete report view'}), 500
