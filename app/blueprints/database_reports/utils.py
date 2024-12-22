def format_value(value, format_type):
    """Format a value based on its type"""
    if value is None:
        return ''
    
    if format_type == 'number':
        return f"{value:,}"
    elif format_type == 'date':
        return value.strftime('%Y-%m-%d') if hasattr(value, 'strftime') else value
    elif format_type == 'datetime':
        return value.strftime('%Y-%m-%d %H:%M:%S') if hasattr(value, 'strftime') else value
    elif format_type == 'boolean':
        return 'Yes' if value else 'No'
    else:
        return str(value)

def execute_query(connection, query):
    """Execute a query on a database connection"""
    from vault_utility import VaultUtility
    import oracledb
    import mysql.connector
    import sqlite3
    
    vault = VaultUtility()
    creds = vault.get_secret(connection.vault_path)
    
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
    
    # Get column names
    columns = [desc[0] for desc in cursor.description]
    
    # Fetch data
    raw_data = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return columns, raw_data

def validate_sql_query(query):
    """Validate that a query is a SELECT statement"""
    if not query or not isinstance(query, str):
        raise ValueError("Query must be a non-empty string")
        
    cleaned_query = query.strip().upper()
    if not cleaned_query.startswith('SELECT'):
        raise ValueError("Only SELECT queries are allowed")
        
    return True
