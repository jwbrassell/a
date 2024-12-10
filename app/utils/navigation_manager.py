from flask_login import current_user
from app.models import NavigationCategory, PageRouteMapping
from sqlalchemy import and_
from app.utils.route_manager import route_to_endpoint
from flask import current_app

class NavigationManager:
    @staticmethod
    def get_user_navigation():
        """
        Build the navigation structure for the current user based on:
        1. User's roles (RBAC)
        2. Navigation category weights
        3. Route weights within categories
        4. Show in navbar setting
        5. Route existence validation
        
        Returns:
            dict: Navigation structure with categories and routes
        """
        if not current_user or not current_user.is_authenticated:
            return {'categories': [], 'uncategorized': []}

        # Get user's roles
        user_roles = {role.name for role in current_user.roles}
        
        # Get all categories ordered by weight
        categories = NavigationCategory.query.order_by(NavigationCategory.weight).all()
        
        # Get all visible route mappings ordered by weight
        route_mappings = PageRouteMapping.query.filter_by(show_in_navbar=True).order_by(PageRouteMapping.weight).all()
        
        # Filter routes based on user roles and route existence
        accessible_routes = []
        for route in route_mappings:
            # Check if route exists
            endpoint = route_to_endpoint(route.route)
            if not endpoint or endpoint not in current_app.view_functions:
                current_app.logger.warning(f"Skipping non-existent route: {route.route}")
                continue
                
            # Check role access
            route_roles = {role.name for role in route.allowed_roles}
            if not route_roles or route_roles & user_roles:  # If no roles specified or user has required role
                accessible_routes.append(route)

        # Organize routes by category
        nav_structure = {
            'categories': [],
            'uncategorized': []
        }

        # Process categorized routes
        for category in categories:
            category_routes = [
                route for route in accessible_routes 
                if route.category_id == category.id
            ]
            
            if category_routes:  # Only include categories that have accessible routes
                nav_structure['categories'].append({
                    'name': category.name,
                    'icon': category.icon,
                    'weight': category.weight,
                    'routes': sorted(category_routes, key=lambda x: x.weight)
                })

        # Process uncategorized routes
        nav_structure['uncategorized'] = sorted(
            [route for route in accessible_routes if route.category_id is None],
            key=lambda x: x.weight
        )

        return nav_structure

    @staticmethod
    def get_breadcrumb(current_route):
        """
        Generate breadcrumb navigation for the current route.
        
        Args:
            current_route: The current route path
            
        Returns:
            list: List of breadcrumb items (name, url)
        """
        breadcrumb = [{'name': 'Home', 'url': '/'}]
        
        try:
            # Find the current route in mappings
            route_mapping = PageRouteMapping.query.filter_by(route=current_route).first()
            if route_mapping:
                # Verify route exists
                endpoint = route_to_endpoint(route_mapping.route)
                if not endpoint or endpoint not in current_app.view_functions:
                    current_app.logger.warning(f"Skipping non-existent route in breadcrumb: {route_mapping.route}")
                    return breadcrumb
                    
                # Add category if exists
                if route_mapping.nav_category:
                    breadcrumb.append({
                        'name': route_mapping.nav_category.name,
                        'url': '#'
                    })
                
                # Add current page
                breadcrumb.append({
                    'name': route_mapping.page_name,
                    'url': None  # Current page has no URL
                })
        except Exception as e:
            current_app.logger.error(f"Error generating breadcrumb for route {current_route}: {str(e)}")
            
        return breadcrumb
