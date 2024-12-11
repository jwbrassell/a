"""Script to collect comprehensive system information about routes, roles, and plugins."""

from flask import current_app
from app import create_app, db
from app.models import Role, PageRouteMapping, NavigationCategory, User
from app.utils.route_manager import route_to_endpoint
from collections import defaultdict

def format_methods(methods):
    """Format HTTP methods consistently."""
    return ', '.join(sorted(list(methods)))

def format_roles(roles):
    """Format role lists consistently."""
    return ', '.join(sorted(roles))

def get_navigation_structure():
    """Get the complete navigation structure with nested categories and routes."""
    categories = {}
    for cat in NavigationCategory.query.order_by(NavigationCategory.weight).all():
        routes = []
        for route in cat.routes:
            if route.show_in_navbar:  # Only include routes that should show in navbar
                roles = [role.name for role in route.allowed_roles]
                routes.append({
                    'name': route.page_name,
                    'path': route.route,
                    'roles': roles,
                    'icon': route.icon,
                    'weight': route.weight,
                    'show_in_navbar': route.show_in_navbar
                })
        
        # Sort routes by weight
        routes.sort(key=lambda x: x['weight'])
        
        categories[cat.name] = {
            'icon': cat.icon,
            'weight': cat.weight,
            'description': cat.description,
            'routes': routes
        }
    
    return categories

def get_uncategorized_routes():
    """Get routes that aren't assigned to any navigation category."""
    uncategorized = []
    seen_routes = set()  # To prevent duplicates
    
    for route in PageRouteMapping.query.filter_by(category_id=None).all():
        if route.show_in_navbar and route.route not in seen_routes:
            seen_routes.add(route.route)
            roles = [role.name for role in route.allowed_roles]
            uncategorized.append({
                'name': route.page_name,
                'path': route.route,
                'roles': roles,
                'icon': route.icon,
                'weight': route.weight
            })
    return sorted(uncategorized, key=lambda x: (x['weight'], x['name']))

def get_role_information():
    """Get all roles and their associated routes."""
    roles = {}
    for role in Role.query.all():
        navbar_routes = []
        other_routes = []
        seen_routes = set()  # To prevent duplicates
        
        for route in role.page_routes:
            if route.route not in seen_routes:
                seen_routes.add(route.route)
                route_info = {
                    'name': route.page_name,
                    'path': route.route,
                    'category': route.nav_category.name if route.nav_category else None
                }
                if route.show_in_navbar:
                    navbar_routes.append(route_info)
                else:
                    other_routes.append(route_info)
        
        roles[role.name] = {
            'icon': role.icon,
            'notes': role.notes,
            'navbar_routes': sorted(navbar_routes, key=lambda x: x['name']),
            'other_routes': sorted(other_routes, key=lambda x: x['name']),
            'user_count': len(role.users)
        }
    return roles

def get_plugin_routes(app):
    """Get routes organized by plugin."""
    plugin_routes = defaultdict(lambda: {'navbar': [], 'api': []})
    seen_routes = set()  # To prevent duplicates
    
    for rule in app.url_map.iter_rules():
        if '.' in rule.endpoint:
            plugin_name = rule.endpoint.split('.')[0]
            if plugin_name not in ['static', 'main']:
                mapping = PageRouteMapping.query.filter_by(route=rule.rule).first()
                
                # Skip if we've already processed this route
                route_key = f"{plugin_name}:{rule.rule}"
                if route_key in seen_routes:
                    continue
                seen_routes.add(route_key)
                
                route_info = {
                    'endpoint': rule.endpoint,
                    'path': rule.rule,
                    'methods': sorted(list(rule.methods)),
                    'page_name': mapping.page_name if mapping else None,
                    'roles': [role.name for role in mapping.allowed_roles] if mapping else ['admin'],
                    'category': mapping.nav_category.name if mapping and mapping.nav_category else None,
                    'show_in_navbar': mapping.show_in_navbar if mapping else False
                }
                
                if mapping and mapping.show_in_navbar:
                    plugin_routes[plugin_name]['navbar'].append(route_info)
                else:
                    plugin_routes[plugin_name]['api'].append(route_info)
    
    # Sort routes within each plugin
    result = {}
    for plugin in plugin_routes:
        result[plugin] = {
            'navbar': sorted(plugin_routes[plugin]['navbar'], key=lambda x: x['endpoint']),
            'api': sorted(plugin_routes[plugin]['api'], key=lambda x: x['endpoint'])
        }
    
    return dict(result)

def check_system():
    """Collect and display comprehensive system information."""
    app = create_app()
    with app.app_context():
        print("\n=== Navigation Structure ===")
        nav_structure = get_navigation_structure()
        for cat_name, cat_info in nav_structure.items():
            print(f"\nCategory: {cat_name}")
            print(f"Icon: {cat_info['icon']}")
            print(f"Weight: {cat_info['weight']}")
            if cat_info['description']:
                print(f"Description: {cat_info['description']}")
            
            if cat_info['routes']:
                print("\nRoutes:")
                for route in cat_info['routes']:
                    print(f"  - {route['name']} ({route['path']})")
                    print(f"    Icon: {route['icon']}")
                    print(f"    Weight: {route['weight']}")
                    print(f"    Roles: {format_roles(route['roles'])}")
        
        uncategorized = get_uncategorized_routes()
        if uncategorized:
            print("\nUncategorized Routes:")
            for route in uncategorized:
                print(f"  - {route['name']} ({route['path']})")
                print(f"    Icon: {route['icon']}")
                print(f"    Weight: {route['weight']}")
                print(f"    Roles: {format_roles(route['roles'])}")
        
        print("\n=== Roles and Access ===")
        roles = get_role_information()
        for role_name, role_info in roles.items():
            print(f"\nRole: {role_name}")
            print(f"Icon: {role_info['icon']}")
            if role_info['notes']:
                print(f"Notes: {role_info['notes']}")
            print(f"Users with this role: {role_info['user_count']}")
            
            if role_info['navbar_routes']:
                print("\nNavbar Routes:")
                for route in role_info['navbar_routes']:
                    category_info = f" (in {route['category']})" if route['category'] else ""
                    print(f"  - {route['name']} ({route['path']}){category_info}")
            
            if role_info['other_routes']:
                print("\nOther Routes:")
                for route in role_info['other_routes']:
                    category_info = f" (in {route['category']})" if route['category'] else ""
                    print(f"  - {route['name']} ({route['path']}){category_info}")
        
        print("\n=== Plugin Routes ===")
        plugin_routes = get_plugin_routes(app)
        for plugin, routes in plugin_routes.items():
            print(f"\nPlugin: {plugin}")
            
            if routes['navbar']:
                print("\nNavbar Routes:")
                for route in routes['navbar']:
                    print(f"  - {route['page_name']} ({route['path']})")
                    print(f"    Roles: {format_roles(route['roles'])}")
                    if route['category']:
                        print(f"    Category: {route['category']}")
            
            if routes['api']:
                print("\nAPI/Other Routes:")
                for route in routes['api']:
                    print(f"  Endpoint: {route['endpoint']}")
                    print(f"  Path: {route['path']}")
                    print(f"  Methods: {format_methods(route['methods'])}")
                    if route['page_name']:
                        print(f"  Page Name: {route['page_name']}")
                    print(f"  Roles: {format_roles(route['roles'])}")
                    if route['category']:
                        print(f"  Category: {route['category']}")

if __name__ == '__main__':
    check_system()
