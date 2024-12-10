"""Script to add created_by columns to project tables."""

from app import create_app, db
import sqlite3

def add_created_by_columns():
    """Add created_by columns to project tables."""
    app = create_app()
    with app.app_context():
        # Get database path from app config
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Add columns and set default values
            tables = [
                'project_status',
                'project_priority',
                'project',
                'task',
                'todo',
                'comment',
                'history'
            ]
            
            for table in tables:
                print(f"\nProcessing {table}...")
                try:
                    # Add created_by column
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN created_by VARCHAR(100);")
                    print(f"Added created_by column to {table}")
                    
                    # Set default value
                    cursor.execute(f"UPDATE {table} SET created_by = 'system';")
                    print(f"Set default value for created_by in {table}")
                    
                    # Make column NOT NULL
                    # SQLite doesn't support ALTER COLUMN, so we need to do this differently
                    # For now, we'll just ensure all values are set
                    cursor.execute(f"UPDATE {table} SET created_by = 'system' WHERE created_by IS NULL;")
                    print(f"Ensured no NULL values in created_by for {table}")
                    
                except Exception as e:
                    print(f"Error processing {table}: {str(e)}")
            
            # Commit changes
            conn.commit()
            print("\nSuccessfully added created_by columns")
            
        except Exception as e:
            conn.rollback()
            print(f"Error: {str(e)}")
            
        finally:
            conn.close()

if __name__ == '__main__':
    add_created_by_columns()
