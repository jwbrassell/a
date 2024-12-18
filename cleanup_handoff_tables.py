import sqlite3
import os

def cleanup_database():
    db_path = 'instance/app.db'
    
    # Delete the database file if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Deleted database file: {db_path}")
    
    # Create a new empty database
    conn = sqlite3.connect(db_path)
    conn.close()
    print("Created new empty database")

if __name__ == '__main__':
    cleanup_database()
