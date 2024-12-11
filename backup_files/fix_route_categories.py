"""Script to fix route categories and re-register routes."""

import sqlite3
import os

def fix_route_categories():
    """Re-register routes with correct categories."""
    db_path = os.path.join('instance', 'app.db')
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("\nFixing route categories...")

        # Get or create Tools category
        cursor.execute("""
            INSERT OR IGNORE INTO navigation_category (name, icon, weight, description, created_by)
            VALUES ('Tools', 'fa-tools', 200, 'System tools and utilities', 'system')
        """)
        
        cursor.execute("SELECT id FROM navigation_category WHERE name = 'Tools'")
        tools_category_id = cursor.fetchone()[0]

        # Get user role id
        cursor.execute("SELECT id FROM role WHERE name = 'user'")
        user_role_id = cursor.fetchone()[0]

        # Clear existing dispatch routes and their role associations
        cursor.execute("""
            DELETE FROM page_route_roles 
            WHERE page_route_id IN (
                SELECT id FROM page_route_mapping 
                WHERE route IN ('dispatch.index', '/dispatch/', '/dispatch/manage')
            )
        """)
        cursor.execute("""
            DELETE FROM page_route_mapping 
            WHERE route IN ('dispatch.index', '/dispatch/', '/dispatch/manage')
        """)

        # Add new dispatch routes
        cursor.execute("""
            INSERT INTO page_route_mapping (route, page_name, icon, weight, category_id, show_in_navbar)
            VALUES ('dispatch.index', 'Dispatch Tool', 'fa-paper-plane', 300, ?, 1)
        """, (tools_category_id,))
        dispatch_route_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO page_route_mapping (route, page_name, icon, weight, category_id, show_in_navbar)
            VALUES ('/dispatch/manage', 'Manage Dispatch', 'fa-cog', 310, ?, 1)
        """, (tools_category_id,))
        manage_route_id = cursor.lastrowid

        # Add role associations using INSERT OR IGNORE
        cursor.execute("""
            INSERT OR IGNORE INTO page_route_roles (page_route_id, role_id) 
            VALUES (?, ?)
        """, (dispatch_route_id, user_role_id))
        
        cursor.execute("""
            INSERT OR IGNORE INTO page_route_roles (page_route_id, role_id) 
            VALUES (?, ?)
        """, (manage_route_id, user_role_id))

        conn.commit()
        print("Route categories have been fixed.")

    except sqlite3.Error as e:
        print(f"Database error: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    fix_route_categories()
