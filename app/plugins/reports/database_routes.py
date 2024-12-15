"""Database connection management routes for Reports plugin."""

from datetime import datetime
from flask import jsonify, request, render_template, current_app, abort
from flask_login import login_required, current_user
from sqlalchemy import inspect
from app import db
from app.utils.enhanced_rbac import requires_permission
from .models import DatabaseConnection
from .vault_utils import vault_manager

def register_routes(bp):
    """Register database routes with blueprint."""
    
    @bp.route('/databases')
    @login_required
    @requires_permission('reports_manage_db', 'read')
    def manage_databases():
        """Display database management interface."""
        databases = DatabaseConnection.query.filter_by(is_active=True, deleted_at=None).all()
        return render_template('reports/manage_databases.html', databases=databases)

    @bp.route('/api/databases')
    @login_required
    @requires_permission('reports_manage_db', 'read')
    def list_databases():
        """List all database connections."""
        databases = DatabaseConnection.query.filter_by(is_active=True, deleted_at=None).all()
        return jsonify([{
            'id': db.id,
            'name': db.name,
            'description': db.description,
            'db_type': db.db_type
        } for db in databases])

    @bp.route('/api/database/<int:db_id>/tables')
    @login_required
    @requires_permission('reports_access', 'read')
    def get_database_tables(db_id):
        """Get tables and their structure for a specific database."""
        db_conn = db.session.query(DatabaseConnection).filter_by(
            id=db_id, 
            is_active=True, 
            deleted_at=None
        ).first()
        if not db_conn:
            abort(404)
        
        try:
            # Get database engine with credentials from vault
            engine = get_db_engine(db_conn)

            # Get inspector
            inspector = inspect(engine)
            
            # Get all tables and their columns
            tables = {}
            for table_name in inspector.get_table_names():
                columns = []
                for column in inspector.get_columns(table_name):
                    columns.append({
                        'name': column['name'],
                        'type': str(column['type']),
                        'nullable': column.get('nullable', True)
                    })
                tables[table_name] = columns

            return jsonify(tables)
        except Exception as e:
            current_app.logger.error(f"Error getting tables for database {db_id}: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @bp.route('/api/database', methods=['POST'])
    @login_required
    @requires_permission('reports_manage_db', 'write')
    def create_database_connection():
        """Create a new database connection."""
        data = request.json
        
        # Create database connection without password
        connection = DatabaseConnection(
            name=data['name'],
            description=data.get('description', ''),
            db_type=data['db_type'],
            host=data.get('host'),
            port=data.get('port'),
            database=data['database'],
            username=data.get('username'),
            created_by=current_user.id,
            updated_by=current_user.id
        )
        
        try:
            # Store credentials in vault only if not SQLite
            if data['db_type'] != 'sqlite' and 'password' in data:
                vault_manager.store_database_credentials(
                    connection.id,
                    {'password': data['password']}
                )
            
            # Save database connection
            db.session.add(connection)
            db.session.commit()
            
            return jsonify({
                'id': connection.id,
                'name': connection.name,
                'description': connection.description,
                'db_type': connection.db_type
            })
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating database connection: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @bp.route('/api/database/<int:db_id>', methods=['PUT'])
    @login_required
    @requires_permission('reports_manage_db', 'write')
    def update_database_connection(db_id):
        """Update an existing database connection."""
        connection = db.session.query(DatabaseConnection).filter_by(
            id=db_id, 
            deleted_at=None
        ).first()
        if not connection:
            abort(404)
        data = request.json
        
        try:
            # Update database connection
            connection.name = data.get('name', connection.name)
            connection.description = data.get('description', connection.description)
            connection.host = data.get('host', connection.host)
            connection.port = data.get('port', connection.port)
            connection.database = data.get('database', connection.database)
            connection.username = data.get('username', connection.username)
            connection.updated_by = current_user.id
            connection.updated_at = datetime.utcnow()
            
            # Update password in vault if provided and not SQLite
            if connection.db_type != 'sqlite' and 'password' in data:
                vault_manager.update_database_credentials(
                    connection.id,
                    {'password': data['password']}
                )
            
            db.session.commit()
            
            return jsonify({
                'id': connection.id,
                'name': connection.name,
                'description': connection.description,
                'db_type': connection.db_type
            })
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating database connection: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @bp.route('/api/database/<int:db_id>', methods=['DELETE'])
    @login_required
    @requires_permission('reports_manage_db', 'write')
    def delete_database_connection(db_id):
        """Soft delete a database connection."""
        connection = db.session.query(DatabaseConnection).filter_by(
            id=db_id, 
            deleted_at=None
        ).first()
        if not connection:
            abort(404)
            
        try:
            # Delete credentials from vault only if not SQLite
            if connection.db_type != 'sqlite':
                vault_manager.delete_database_credentials(connection.id)
            
            # Soft delete connection
            connection.is_active = False
            connection.deleted_at = datetime.utcnow()
            connection.updated_by = current_user.id
            connection.updated_at = datetime.utcnow()
            db.session.commit()
            
            return '', 204
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error deleting database connection: {str(e)}")
            return jsonify({'error': str(e)}), 500
