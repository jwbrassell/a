from flask import Blueprint, render_template, request, jsonify, current_app, abort, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import create_engine, text, inspect, or_
from app import db
from app.utils.rbac import requires_roles
from .models import DatabaseConnection, ReportView
import json
from decimal import Decimal
import re
import datetime

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)

# Blueprint is now created in __init__.py
from . import bp

def apply_transform(value, transform_config):
    """Apply server-side transformation to a value."""
    if not transform_config or not transform_config.get('type'):
        return value

    try:
        transform_type = transform_config['type']
        
        if transform_type == 'python':
            # Create a safe environment with limited builtins
            safe_globals = {
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
                'len': len,
                'list': list,
                'dict': dict,
                'set': set,
                'tuple': tuple,
                'datetime': datetime,
                're': re,
                'value': value
            }
            code = transform_config.get('code', '')
            # Add return if not present
            if 'return' not in code:
                code = f"return {code}"
            return eval(code, safe_globals)
            
        elif transform_type == 'regex':
            pattern = transform_config.get('pattern', '')
            replacement = transform_config.get('replacement', '')
            flags = 0
            if transform_config.get('case_insensitive'):
                flags |= re.IGNORECASE
            if transform_config.get('multiline'):
                flags |= re.MULTILINE
            
            if transform_config.get('match_only', False):
                match = re.search(pattern, str(value), flags)
                return match.group(0) if match else value
            elif transform_config.get('extract_group') is not None:
                match = re.search(pattern, str(value), flags)
                if match and transform_config['extract_group'] < len(match.groups()):
                    return match.group(transform_config['extract_group'] + 1)
                return value
            else:
                return re.sub(pattern, replacement, str(value), flags=flags)
            
        return value
        
    except Exception as e:
        current_app.logger.error(f"Transform error: {str(e)}")
        return value

@bp.route('/')
@login_required
def index():
    """Display the reports dashboard with available views."""
    views = db.session.query(ReportView).filter(
        or_(
            ReportView.created_by == current_user.id,
            ReportView.is_private.is_(False)
        )
    ).all()
    return render_template('reports/dashboard.html', views=views)

@bp.route('/databases')
@login_required
@requires_roles('admin')
def manage_databases():
    """Display database management interface."""
    databases = DatabaseConnection.query.filter_by(is_active=True).all()
    return render_template('reports/manage_databases.html', databases=databases)

@bp.route('/view/new', methods=['GET', 'POST'])
@login_required
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
            created_by=current_user.id
        )
        
        # Add role permissions if specified
        if 'roles' in data:
            from app.models import Role
            roles = Role.query.filter(Role.id.in_(data['roles'])).all()
            view.roles = roles

        db.session.add(view)
        db.session.commit()
        return jsonify(view.to_dict())

    databases = DatabaseConnection.query.filter_by(is_active=True).all()
    return render_template('reports/create_view.html', databases=databases)

@bp.route('/view/<int:view_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_view(view_id):
    """Edit an existing report view."""
    view = db.session.query(ReportView).get(view_id)
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

        # Update role permissions if specified
        if 'roles' in data:
            from app.models import Role
            roles = Role.query.filter(Role.id.in_(data['roles'])).all()
            view.roles = roles

        db.session.commit()
        return jsonify(view.to_dict())

    databases = DatabaseConnection.query.filter_by(is_active=True).all()
    return render_template('reports/edit_view.html', view=view, databases=databases)

@bp.route('/view/<int:view_id>')
@login_required
def view_report(view_id):
    """Display a specific report view."""
    view = db.session.query(ReportView).get(view_id)
    if not view:
        abort(404)
    
    # Check permissions
    if view.is_private and view.created_by != current_user.id:
        if not any(role in view.roles for role in current_user.roles):
            return jsonify({'error': 'Access denied'}), 403
    
    # Verify database connection exists and is active
    if not view.database or not view.database.is_active:
        return render_template('reports/view.html', view=view, error="Database connection not found or inactive")
    
    return render_template('reports/view.html', view=view)

@bp.route('/api/view/<int:view_id>', methods=['DELETE'])
@login_required
def delete_view(view_id):
    """Delete a report view."""
    view = db.session.query(ReportView).get(view_id)
    if not view:
        abort(404)
    
    # Check permissions
    if view.created_by != current_user.id and not current_user.has_role('admin'):
        return jsonify({'error': 'Access denied'}), 403
    
    db.session.delete(view)
    db.session.commit()
    return '', 204

@bp.route('/api/view/<int:view_id>/data')
@login_required
def get_view_data(view_id):
    """Get data for a specific view."""
    view = db.session.query(ReportView).get(view_id)
    if not view:
        return jsonify({'error': 'Report view not found'}), 404
    
    # Check permissions
    if view.is_private and view.created_by != current_user.id:
        if not any(role in view.roles for role in current_user.roles):
            return jsonify({'error': 'Access denied'}), 403

    # Verify database connection exists and is active
    if not view.database:
        return jsonify({'error': 'Database connection not found'}), 404
    if not view.database.is_active:
        return jsonify({'error': 'Database connection is inactive'}), 400

    try:
        # Get database connection
        db_conn = view.database
        
        # Create engine based on database type
        if db_conn.db_type == 'sqlite':
            engine = create_engine(f'sqlite:///{db_conn.database}')
        else:
            # Use mysqlclient format for MySQL/MariaDB
            engine = create_engine(
                f'mysql://{db_conn.username}:{db_conn.password}@{db_conn.host}:{db_conn.port}/{db_conn.database}'
            )

        # Execute query
        with engine.connect() as conn:
            result = conn.execute(text(view.query))
            columns = result.keys()
            data = []
            for row in result:
                row_dict = {}
                for idx, col in enumerate(columns):
                    value = row[idx]
                    if isinstance(value, (datetime.date, datetime.datetime)):
                        value = value.isoformat()
                    elif isinstance(value, Decimal):
                        value = str(value)
                    elif value is None:
                        value = None
                    row_dict[col] = value
                data.append(row_dict)

            # Update last_run timestamp
            view.last_run = datetime.datetime.utcnow()
            db.session.commit()

            # Log the response data structure
            current_app.logger.info(f"Column config: {json.dumps(view.column_config)}")
            current_app.logger.info(f"Sample data: {json.dumps(data[0]) if data else 'No data'}")

            return jsonify({
                'data': data,
                'columns': view.column_config
            })
    except Exception as e:
        current_app.logger.error(f"Error executing query for view {view_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/databases')
@login_required
@requires_roles('admin')
def list_databases():
    """List all database connections."""
    databases = DatabaseConnection.query.filter_by(is_active=True).all()
    return jsonify([{
        'id': db.id,
        'name': db.name,
        'description': db.description,
        'db_type': db.db_type
    } for db in databases])

@bp.route('/api/database/<int:db_id>/tables')
@login_required
def get_database_tables(db_id):
    """Get tables and their structure for a specific database."""
    db_conn = db.session.query(DatabaseConnection).get(db_id)
    if not db_conn:
        abort(404)
    
    try:
        # Create engine based on database type
        if db_conn.db_type == 'sqlite':
            engine = create_engine(f'sqlite:///{db_conn.database}')
        else:
            # Use mysqlclient format for MySQL/MariaDB
            engine = create_engine(
                f'mysql://{db_conn.username}:{db_conn.password}@{db_conn.host}:{db_conn.port}/{db_conn.database}'
            )

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
@requires_roles('admin')
def create_database_connection():
    """Create a new database connection."""
    data = request.json
    
    connection = DatabaseConnection(
        name=data['name'],
        description=data.get('description', ''),
        db_type=data['db_type'],
        host=data.get('host'),
        port=data.get('port'),
        database=data['database'],
        username=data.get('username'),
        password=data.get('password'),
        created_by=current_user.id
    )
    
    db.session.add(connection)
    db.session.commit()
    
    return jsonify({
        'id': connection.id,
        'name': connection.name,
        'description': connection.description,
        'db_type': connection.db_type
    })

@bp.route('/api/database/<int:db_id>', methods=['PUT'])
@login_required
@requires_roles('admin')
def update_database_connection(db_id):
    """Update an existing database connection."""
    connection = db.session.query(DatabaseConnection).get(db_id)
    if not connection:
        abort(404)
    data = request.json
    
    connection.name = data.get('name', connection.name)
    connection.description = data.get('description', connection.description)
    connection.host = data.get('host', connection.host)
    connection.port = data.get('port', connection.port)
    connection.database = data.get('database', connection.database)
    connection.username = data.get('username', connection.username)
    if 'password' in data:
        connection.password = data['password']
    
    db.session.commit()
    
    return jsonify({
        'id': connection.id,
        'name': connection.name,
        'description': connection.description,
        'db_type': connection.db_type
    })

@bp.route('/api/database/<int:db_id>', methods=['DELETE'])
@login_required
@requires_roles('admin')
def delete_database_connection(db_id):
    """Soft delete a database connection."""
    connection = db.session.query(DatabaseConnection).get(db_id)
    if not connection:
        abort(404)
    connection.is_active = False
    db.session.commit()
    return '', 204

@bp.route('/api/test-query', methods=['POST'])
@login_required
def test_query():
    """Test a query and return column information."""
    data = request.json
    db_conn = db.session.query(DatabaseConnection).get(data['database_id'])
    if not db_conn:
        abort(404)
    
    try:
        # Create engine based on database type
        if db_conn.db_type == 'sqlite':
            engine = create_engine(f'sqlite:///{db_conn.database}')
        else:
            # Use mysqlclient format for MySQL/MariaDB
            engine = create_engine(
                f'mysql://{db_conn.username}:{db_conn.password}@{db_conn.host}:{db_conn.port}/{db_conn.database}'
            )

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
