from app import db
from app.models import Role, PageRouteMapping
from flask import current_app
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

# Cache for validated routes
_route_cache = {}

def _init_route_cache():
    """Initialize the route cache with known mappings."""
    global _route_cache
    _route_cache = {}

def get_actual_endpoint(endpoint):
    """Get the actual Flask endpoint for a given route or endpoint."""
    # Initialize cache if empty
    if not _route_cache:
        _init_route_cache()
    
    # Check cache first
    if endpoint in _route_cache:
        return _route_cache[endpoint]
    
    # If not in cache, try to find the actual endpoint
    try:
        # Get all registered Flask endpoints
        if current_app:
            for rule in current_app.url_map.iter_rules():
                if rule.endpoint == endpoint:
                    _route_cache[endpoint] = endpoint
                    return endpoint
                # Check if the endpoint matches when normalized
                if rule.endpoint.replace('_', '-') == endpoint.replace('_', '-'):
                    _route_cache[endpoint] = rule.endpoint
                    return rule.endpoint
    except Exception as e:
        logger.error(f"Error finding actual endpoint for {endpoint}: {str(e)}")
    
    # If no match found, return None to indicate invalid endpoint
    return None

@lru_cache(maxsize=128)
def route_to_endpoint(route):
    """Convert a route path to a Flask endpoint name. Returns None if endpoint doesn't exist."""
    # Initialize cache if empty
    if not _route_cache:
        _init_route_cache()
    
    # If the route is in our cache, return the mapped endpoint
    if route in _route_cache:
        return _route_cache[route]
    
    # If it's already in endpoint format (contains a dot), verify it's valid
    if '.' in route:
        actual_endpoint = get_actual_endpoint(route)
        if actual_endpoint:
            _route_cache[route] = actual_endpoint
            return actual_endpoint
        return None

    # Handle plugin routes
    if route.startswith('/'):
        parts = route.lstrip('/').split('/')
        if len(parts) > 1:
            # Convert URL path to endpoint format
            endpoint = f"{parts[0]}.{parts[1]}" if len(parts) > 1 else f"{parts[0]}.index"
            actual_endpoint = get_actual_endpoint(endpoint)
            if actual_endpoint:
                _route_cache[route] = actual_endpoint
                return actual_endpoint
            return None
    
    # Default handling
    endpoint = route.lstrip('/').replace('/', '.')
    if endpoint == '':
        return 'main.index'  # Special case for root route
    elif '.' not in endpoint:
        endpoint = f'main.{endpoint}'  # Add main blueprint prefix if no blueprint specified

    # Replace hyphens with underscores in endpoint names
    endpoint = endpoint.replace('-', '_')
    
    # Verify the endpoint exists
    actual_endpoint = get_actual_endpoint(endpoint)
    if actual_endpoint:
        _route_cache[route] = actual_endpoint
        return actual_endpoint
    
    return None

def cleanup_invalid_routes():
    """Remove route mappings for endpoints that no longer exist.
    
    Returns:
        tuple: (number of routes removed, list of removed route names)
    """
    try:
        removed_count = 0
        removed_routes = []
        
        # Get all route mappings
        route_mappings = PageRouteMapping.query.all()
        
        for mapping in route_mappings:
            # Check if the endpoint exists
            endpoint = route_to_endpoint(mapping.route)
            if not endpoint or endpoint not in current_app.view_functions:
                # Log the removal
                logger.info(f"Removing invalid route mapping: {mapping.route} -> {mapping.page_name}")
                removed_routes.append(mapping.route)
                removed_count += 1
                
                # Remove the mapping
                db.session.delete(mapping)
        
        # Commit changes if any routes were removed
        if removed_count > 0:
            db.session.commit()
            logger.info(f"Removed {removed_count} invalid route mappings")
        
        return removed_count, removed_routes
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error cleaning up invalid routes: {str(e)}")
        return 0, []

def map_route_to_roles(route_path, page_name, roles=None, category_id=None, icon='fa-link', weight=0):
    """Map a route to specific roles and create/update the PageRouteMapping."""
    try:
        # First check if the route exists in Flask's URL map
        route_exists = False
        actual_route = None
        for rule in current_app.url_map.iter_rules():
            if rule.rule == route_path:
                route_exists = True
                actual_route = route_path
                break
            # Also check if it matches when converted to endpoint
            elif route_to_endpoint(route_path) == rule.endpoint:
                route_exists = True
                actual_route = rule.rule
                break
        
        if not route_exists:
            logger.warning(f"Attempted to map non-existent route: {route_path}")
            return False
        
        # Get or create the route mapping using the actual route path
        mapping = PageRouteMapping.query.filter_by(route=actual_route).first()
        if not mapping:
            mapping = PageRouteMapping(
                route=actual_route,
                page_name=page_name,
                category_id=category_id,
                icon=icon,
                weight=weight
            )
            db.session.add(mapping)
        else:
            # Update existing mapping
            mapping.page_name = page_name
            mapping.category_id = category_id
            mapping.icon = icon
            mapping.weight = weight
        
        # Clear existing role associations
        mapping.allowed_roles = []
        
        # If no roles specified, restrict to admin by default
        if roles is None:
            roles = ['admin']
        
        # Add role associations
        for role_name in roles:
            role = Role.query.filter_by(name=role_name).first()
            if role:
                mapping.allowed_roles.append(role)
            else:
                logger.warning(f"Role '{role_name}' not found when mapping route '{actual_route}'")
        
        db.session.commit()
        logger.info(f"Successfully mapped route '{actual_route}' to roles: {roles}")
        return True
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error mapping route '{route_path}' to roles: {str(e)}")
        return False

def get_route_roles(route_path):
    """Get all roles associated with a route."""
    try:
        # Convert route_path to actual endpoint
        endpoint = route_to_endpoint(route_path)
        if not endpoint:
            return ['admin']  # Default roles for invalid routes
            
        mapping = PageRouteMapping.query.filter_by(route=endpoint).first()
        
        # If no mapping exists, return default roles (admin only)
        if not mapping:
            return ['admin']
            
        return [role.name for role in mapping.allowed_roles]
        
    except Exception as e:
        logger.error(f"Error getting roles for route '{route_path}': {str(e)}")
        return ['admin']  # Default to admin only

def remove_route_mapping(route_path):
    """Remove a route mapping and its role associations."""
    try:
        # Convert route_path to actual endpoint
        endpoint = route_to_endpoint(route_path)
        if not endpoint:
            return False
            
        mapping = PageRouteMapping.query.filter_by(route=endpoint).first()
        if mapping:
            db.session.delete(mapping)
            db.session.commit()
            logger.info(f"Successfully removed mapping for route '{endpoint}'")
            return True
        return False
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error removing mapping for route '{route_path}': {str(e)}")
        return False

def bulk_update_route_mappings(mappings):
    """Update multiple route mappings at once."""
    success_count = 0
    total_count = len(mappings)
    
    for mapping in mappings:
        if map_route_to_roles(
            route_path=mapping['route'],
            page_name=mapping['page_name'],
            roles=mapping.get('roles'),  # If not specified, will default to admin only
            category_id=mapping.get('category_id'),
            icon=mapping.get('icon', 'fa-link'),
            weight=mapping.get('weight', 0)
        ):
            success_count += 1
    
    return success_count, total_count

def sync_blueprint_routes(blueprint_name, route_mappings):
    """Sync route mappings for a specific blueprint."""
    try:
        # Convert blueprint name to handle special cases
        if blueprint_name == 'dispatch-tool':
            blueprint_name = 'dispatch_tool'
            
        # Get all existing mappings for this blueprint
        existing_routes = PageRouteMapping.query.filter(
            PageRouteMapping.route.startswith(f'{blueprint_name}.')
        ).all()
        
        # Create a set of routes that should exist (in endpoint format)
        new_routes = set()
        for mapping in route_mappings:
            endpoint = route_to_endpoint(mapping['route'])
            if endpoint:  # Only include valid endpoints
                new_routes.add(endpoint)
        
        # Remove mappings that shouldn't exist anymore
        for existing in existing_routes:
            if existing.route not in new_routes:
                db.session.delete(existing)
        
        # Update/create new mappings
        success_count, total_count = bulk_update_route_mappings(route_mappings)
        
        db.session.commit()
        logger.info(f"Successfully synced {success_count}/{total_count} routes for blueprint '{blueprint_name}'")
        return True
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error syncing routes for blueprint '{blueprint_name}': {str(e)}")
        return False
