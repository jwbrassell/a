"""Data fetching and query execution routes for Reports plugin."""

from datetime import datetime
from decimal import Decimal
from flask import jsonify, request, current_app
from flask_login import login_required, current_user
from sqlalchemy import text
from app import db
from app.utils.enhanced_rbac import requires_permission
from .models import ReportView, DatabaseConnection
from .database_utils import get_db_engine, apply_transform

def register_routes(bp):
    """Register data routes with blueprint."""

    @bp.route('/api/view/<int:view_id>/data')
    @login_required
    @requires_permission('reports_access', 'read')
    def get_view_data(view_id):
        """Get data for a specific view."""
        view = db.session.query(ReportView).filter_by(
            id=view_id,
            deleted_at=None
        ).first()
        if not view:
            return jsonify({'error': 'Report view not found'}), 404
        
        # Check permissions
        if view.is_private and view.created_by != current_user.id:
            if not any(role in view.roles for role in current_user.roles):
                return jsonify({'error': 'Access denied'}), 403

        # Verify database connection exists and is active
        if not view.database:
            return jsonify({'error': 'Database connection not found'}), 404
        if not view.database.is_active or view.database.deleted_at:
            return jsonify({'error': 'Database connection is inactive'}), 400

        try:
            # Get database engine with credentials from vault
            engine = get_db_engine(view.database)

            # Execute query
            with engine.connect() as conn:
                result = conn.execute(text(view.query))
                columns = result.keys()
                data = []
                for row in result:
                    row_dict = {}
                    for idx, col in enumerate(columns):
                        value = row[idx]
                        # Apply any configured transformations
                        if view.column_config.get(col, {}).get('transform'):
                            value = apply_transform(value, view.column_config[col]['transform'])
                        
                        # Handle special data types
                        if isinstance(value, (datetime.date, datetime.datetime)):
                            value = value.isoformat()
                        elif isinstance(value, Decimal):
                            value = str(value)
                        elif value is None:
                            value = None
                        row_dict[col] = value
                    data.append(row_dict)

                # Update last_run timestamp
                view.last_run = datetime.utcnow()
                view.updated_by = current_user.id
                view.updated_at = datetime.utcnow()
                db.session.commit()

                return jsonify({
                    'data': data,
                    'columns': view.column_config
                })
        except Exception as e:
            current_app.logger.error(f"Error executing query for view {view_id}: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @bp.route('/api/test-query', methods=['POST'])
    @login_required
    @requires_permission('reports_create', 'write')
    def test_query():
        """Test a query and return column information."""
        data = request.json
        db_conn = db.session.query(DatabaseConnection).filter_by(
            id=data['database_id'],
            is_active=True,
            deleted_at=None
        ).first()
        if not db_conn:
            return jsonify({'error': 'Database connection not found'}), 404
        
        try:
            # Get database engine with credentials from vault
            engine = get_db_engine(db_conn)

            # Execute query
            with engine.connect() as conn:
                result = conn.execute(text(data['query']))
                columns = result.keys()
                row = result.fetchone()
                if row is None:
                    return jsonify({'error': 'Query returned no results'}), 400
                
                # Convert row to dict and handle special types
                sample_data = {}
                for idx, col in enumerate(columns):
                    value = row[idx]
                    if isinstance(value, (datetime.date, datetime.datetime)):
                        value = value.isoformat()
                    elif isinstance(value, Decimal):
                        value = str(value)
                    elif value is None:
                        value = None
                    sample_data[col] = value
                
                return jsonify({
                    'columns': list(columns),
                    'sample_data': sample_data
                })
        except Exception as e:
            current_app.logger.error(f"Error testing query: {str(e)}")
            return jsonify({'error': str(e)}), 500
