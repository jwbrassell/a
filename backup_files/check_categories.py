"""Script to check navigation categories."""

from app import create_app, db
from app.models import NavigationCategory, PageRouteMapping

def check_categories():
    """Check and print navigation categories and their routes."""
    app = create_app()
    with app.app_context():
        print("\nNavigation Categories:")
        categories = NavigationCategory.query.all()
        for category in categories:
            print(f"\nCategory: {category.name}")
            print(f"ID: {category.id}")
            print(f"Icon: {category.icon}")
            print(f"Weight: {category.weight}")
            print("Routes:")
            routes = PageRouteMapping.query.filter_by(category_id=category.id).all()
            for route in routes:
                print(f"  - {route.page_name} ({route.route})")

        print("\nUncategorized Routes:")
        uncategorized = PageRouteMapping.query.filter_by(category_id=None).all()
        for route in uncategorized:
            print(f"  - {route.page_name} ({route.route})")

if __name__ == '__main__':
    check_categories()
