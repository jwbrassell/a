from app import create_app, db
import sqlite3
from sqlite3 import Error

def show_table_contents(table_name):
    """Show contents of a specific table in the SQLite database."""
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect('instance/app.db')
        cursor = conn.cursor()
        
        # Get column names
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Get all rows
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        # Print table header
        print(f"\n=== Contents of {table_name} table ===")
        print("Columns:", " | ".join(columns))
        print("-" * 80)
        
        # Print rows
        for row in rows:
            print(" | ".join(str(value) for value in row))
            
        conn.close()
        
    except Error as e:
        print(f"Error accessing database: {e}")

def list_tables():
    """List all tables in the database."""
    try:
        conn = sqlite3.connect('instance/app.db')
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("\nAvailable tables:")
        for idx, table in enumerate(tables, 1):
            print(f"{idx}. {table[0]}")
            
        conn.close()
        return [table[0] for table in tables]
        
    except Error as e:
        print(f"Error accessing database: {e}")
        return []

if __name__ == '__main__':
    # List all tables
    tables = list_tables()
    
    if tables:
        while True:
            try:
                choice = input("\nEnter table number to view (or 'q' to quit): ")
                
                if choice.lower() == 'q':
                    break
                    
                table_idx = int(choice) - 1
                if 0 <= table_idx < len(tables):
                    show_table_contents(tables[table_idx])
                else:
                    print("Invalid table number!")
                    
            except ValueError:
                print("Please enter a valid number or 'q' to quit")
