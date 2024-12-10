"""Script to check database state."""

import sqlite3
import os

def check_db():
    """Check database state."""
    db_path = os.path.join('instance', 'app.db')
    
    print("\nChecking database state...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check page_route_roles table
        print("\nCurrent page_route_roles:")
        cursor.execute("SELECT * FROM page_route_roles")
        for row in cursor.fetchall():
            print(f"page_route_id: {row[0]}, role_id: {row[1]}")
        
        # Check page_route_mapping table
        print("\nCurrent PageRouteMappings:")
        cursor.execute("""
            SELECT prm.id, prm.route, prm.page_name, prm.category_id, nc.name as category_name 
            FROM page_route_mapping prm 
            LEFT JOIN navigation_category nc ON prm.category_id = nc.id
        """)
        for row in cursor.fetchall():
            print(f"id: {row[0]}, route: {row[1]}, page_name: {row[2]}, category: {row[4]}")
            
            # Get roles for this route
            cursor.execute("""
                SELECT r.name 
                FROM role r 
                JOIN page_route_roles prr ON r.id = prr.role_id 
                WHERE prr.page_route_id = ?
            """, (row[0],))
            roles = [r[0] for r in cursor.fetchall()]
            print(f"  roles: {roles}")
        
        # Check navigation categories
        print("\nCurrent Navigation Categories:")
        cursor.execute("SELECT id, name, icon, weight FROM navigation_category")
        for row in cursor.fetchall():
            print(f"id: {row[0]}, name: {row[1]}, icon: {row[2]}, weight: {row[3]}")
            
            # Get routes for this category
            cursor.execute("""
                SELECT page_name, route 
                FROM page_route_mapping 
                WHERE category_id = ?
            """, (row[0],))
            routes = cursor.fetchall()
            if routes:
                print("  Routes:")
                for route in routes:
                    print(f"    - {route[0]} ({route[1]})")
        
        # Check roles
        print("\nCurrent Roles:")
        cursor.execute("SELECT id, name FROM role")
        for row in cursor.fetchall():
            print(f"id: {row[0]}, name: {row[1]}")
            
    except sqlite3.Error as e:
        print(f"Database error: {str(e)}")
    finally:
        conn.close()

if __name__ == '__main__':
    check_db()
