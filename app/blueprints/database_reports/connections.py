from flask import render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from . import bp
from .models import DatabaseConnection
from app.extensions import db
from app.utils.enhanced_rbac import requires_permission
from vault_utility import VaultUtility
import oracledb
import mysql.connector
import sqlite3

# Initialize vault utility
vault = VaultUtility()

@bp.route('/connections')
@login_required
@requires_permission('manage_database_connections')
def list_connections():
    """List all database connections"""
    connections = DatabaseConnection.query.all()
    return render_template('database_reports/connections/list.html', connections=connections)

@bp.route('/connections/new', methods=['GET', 'POST'])
@login_required
@requires_permission('manage_database_connections')
def new_connection():
    """Create a new database connection"""
    if request.method == 'POST':
        try:
            # Create vault path for KV store
            vault_path = f'database_creds/{request.form["name"].lower().replace(" ", "_")}'
            
            # Store credentials in vault using KV store
            vault.store_secret(vault_path, {
                'username': request.form['username'],
                'password': request.form['password']
            })
            
            # Create connection record
            connection = DatabaseConnection(
                name=request.form['name'],
                description=request.form['description'],
                db_type=request.form['db_type'],
                host=request.form.get('host'),
                port=request.form.get('port', type=int),
                database=request.form['database'],
                vault_path=vault_path,
                created_by_id=current_user.id
            )
            db.session.add(connection)
            db.session.commit()
            
            flash('Database connection created successfully', 'success')
            return redirect(url_for('database_reports.list_connections'))
            
        except Exception as e:
            flash(f'Error creating connection: {str(e)}', 'error')
            
    return render_template('database_reports/connections/new.html')

@bp.route('/connections/<int:id>/edit', methods=['POST'])
@login_required
@requires_permission('manage_database_connections')
def edit_connection(id):
    """Edit a database connection"""
    connection = DatabaseConnection.query.get_or_404(id)
    
    try:
        # Update connection details
        connection.name = request.form['name']
        connection.description = request.form['description']
        connection.host = request.form.get('host')
        connection.port = request.form.get('port', type=int)
        connection.database = request.form['database']
        connection.is_active = 'is_active' in request.form
        
        # Update credentials in vault if provided
        if request.form.get('username') and request.form.get('password'):
            vault.store_secret(connection.vault_path, {
                'username': request.form['username'],
                'password': request.form['password']
            })
        
        # Commit changes immediately
        db.session.commit()
        
        # Explicitly refresh the connection object from the database
        db.session.refresh(connection)
        
        flash('Database connection updated successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating connection: {str(e)}', 'error')
    
    return redirect(url_for('database_reports.list_connections'))

@bp.route('/connections/<int:id>/delete', methods=['POST'])
@login_required
@requires_permission('manage_database_connections')
def delete_connection(id):
    """Delete a database connection"""
    connection = DatabaseConnection.query.get_or_404(id)
    
    try:
        # Delete credentials from vault
        vault.delete_secret(connection.vault_path)
        
        # Delete connection from database
        db.session.delete(connection)
        db.session.commit()
        
        flash('Database connection deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting connection: {str(e)}', 'error')
    
    return redirect(url_for('database_reports.list_connections'))

@bp.route('/connections/<int:id>/test')
@login_required
@requires_permission('manage_database_connections')
def test_connection(id):
    """Test database connection"""
    # Get a fresh connection object from the database
    connection = db.session.query(DatabaseConnection).get_or_404(id)
    
    try:
        # Get credentials from vault
        creds = vault.get_secret(connection.vault_path)
        
        # Declare conn variable before conditional assignments
        conn = None
        
        if connection.db_type == 'oracle':
            conn = oracledb.connect(
                user=creds['username'],
                password=creds['password'],
                dsn=f'{connection.host}:{connection.port}/{connection.database}'
            )
        elif connection.db_type == 'mysql':
            conn = mysql.connector.connect(
                host=connection.host,
                port=connection.port,
                user=creds['username'],
                password=creds['password'],
                database=connection.database
            )
        else:  # sqlite
            conn = sqlite3.connect(connection.database)
            
        conn.close()
        return jsonify({'status': 'success', 'message': 'Connection successful'})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})
