"""Script to check existing database tables and their columns."""

from app import create_app, db
import sqlite3

def check_tables():
    """Check existing tables and their columns in the database."""
    app = create_app()
    with app.app_context():
        # Get database path from app config
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("\nExisting tables:")
        for table in tables:
            table_name = table[0]
            print(f"\n{table_name}:")
            
            # Get columns for each table
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  - {col[1]} ({col[2]}) {'NOT NULL' if col[3] else 'NULL'}")
        
        conn.close()

if __name__ == '__main__':
    check_tables()
