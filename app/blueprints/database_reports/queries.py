from flask import request, jsonify
from flask_login import login_required
from .routes import bp
from .models import DatabaseConnection
import oracledb
import mysql.connector
import sqlite3
from vault_utility import VaultUtility

# Initialize vault utility
vault = VaultUtility()

@bp.route('/test_query', methods=['POST'])
@login_required
def test_query():
    """Test SQL query and return column information"""
    try:
        data = request.get_json()
        connection_id = data.get('connection_id')
        query = data.get('query')
        
        if not connection_id or not query:
            return jsonify({'status': 'error', 'message': 'Missing connection_id or query'})
            
        if not query.strip().upper().startswith('SELECT'):
            return jsonify({'status': 'error', 'message': 'Only SELECT queries are allowed'})
        
        connection = DatabaseConnection.query.get_or_404(connection_id)
        creds = vault.get_secret(connection.vault_path)
        
        conn = None
        cursor = None
        
        try:
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
                
            cursor = conn.cursor()
            cursor.execute(query)
            
            # Get column names from cursor description
            columns = [desc[0] for desc in cursor.description]
            
            # Fetch a sample row to determine column types
            sample_row = cursor.fetchone()
            
            # Important: Fetch all remaining rows to avoid 'Unread result found' error
            if connection.db_type == 'mysql':
                cursor.fetchall()
            
            column_types = []
            if sample_row:
                for value in sample_row:
                    if isinstance(value, (int, float)):
                        column_types.append('number')
                    elif isinstance(value, bool):
                        column_types.append('boolean')
                    else:
                        column_types.append('text')
            else:
                column_types = ['text'] * len(columns)
            
            return jsonify({
                'status': 'success',
                'columns': columns,
                'types': column_types
            })
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})
