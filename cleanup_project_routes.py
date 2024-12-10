"""Script to clean up project route mappings."""

from app import create_app, db
from app.models import PageRouteMapping

def cleanup_project_routes():
    """Remove duplicate project route mappings."""
    app = create_app()
    with app.app_context():
        print("\nCurrent route mappings:")
        mappings = PageRouteMapping.query.all()
        for mapping in mappings:
            print(f"- {mapping.route} -> {mapping.page_name}")

        # Delete URL path format routes
        url_paths = ['/projects/', '/projects/create', '/projects/list']
        for path in url_paths:
            mapping = PageRouteMapping.query.filter_by(route=path).first()
            if mapping:
                print(f"\nDeleting mapping: {mapping.route} -> {mapping.page_name}")
                db.session.delete(mapping)

        try:
            db.session.commit()
            print("\nCleanup completed successfully")
        except Exception as e:
            db.session.rollback()
            print(f"\nError during cleanup: {str(e)}")

        print("\nRemaining route mappings:")
        mappings = PageRouteMapping.query.all()
        for mapping in mappings:
            print(f"- {mapping.route} -> {mapping.page_name}")

if __name__ == '__main__':
    cleanup_project_routes()
