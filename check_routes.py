from app import create_app, db
from app.models import PageRouteMapping, NavigationCategory

app = create_app()
with app.app_context():
    print("\nNavigation Categories:")
    categories = NavigationCategory.query.all()
    for category in categories:
        print(f"Category: {category.name} (ID: {category.id})")
        
    print("\nOncall Routes in Database:")
    routes = PageRouteMapping.query.filter(PageRouteMapping.route.like('oncall%')).all()
    for route in routes:
        category_name = route.nav_category.name if route.nav_category else "Uncategorized"
        print(f"Route: {route.route}, Page Name: {route.page_name}, Category: {category_name}")

    print("\nAll Routes in Database:")
    all_routes = PageRouteMapping.query.all()
    for route in all_routes:
        category_name = route.nav_category.name if route.nav_category else "Uncategorized"
        print(f"Route: {route.route}, Page Name: {route.page_name}, Category: {category_name}")
