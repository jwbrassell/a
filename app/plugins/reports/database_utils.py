"""Database utilities for Reports plugin."""

import re
import datetime
from sqlalchemy import create_engine
from flask import current_app

def get_db_engine(db_conn):
    """Create SQLAlchemy engine with credentials from vault."""
    try:
        # SQLite doesn't need credentials from vault
        if db_conn.db_type == 'sqlite':
            engine = create_engine(f'sqlite:///{db_conn.database}')
            return engine
            
        # For other database types, get credentials from vault
        from .vault_utils import vault_manager
        credentials = vault_manager.get_database_credentials(db_conn.id)
        
        # Use mysqlclient format for MySQL/MariaDB
        engine = create_engine(
            f'mysql://{db_conn.username}:{credentials["password"]}@{db_conn.host}:{db_conn.port}/{db_conn.database}'
        )
        return engine
    except Exception as e:
        current_app.logger.error(f"Error creating database engine: {str(e)}")
        raise

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
