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
    
    # If no match found, return original endpoint
    return endpoint

@lru_cache(maxsize=128)
def route_to_endpoint(route):
    """Convert a route path to a Flask endpoint name."""
    # Initialize cache if empty
    if not _route_cache:
        _init_route_cache()
    
    # If the route is in our cache, return the mapped endpoint
    if route in _route_cache:
        return _route_cache[route]
    
    # If it's already in endpoint format (contains a dot), verify it's valid
    if '.' in route:
        actual_endpoint = get_actual_endpoint(route)
        if actual_endpoint != route:
            _route_cache[route] = actual_endpoint
            return actual_endpoint
        return route

    # Remove leading slash and replace remaining slashes with dots
    endpoint = route.lstrip('/').replace('/', '.')
    if endpoint == '':
        return 'main.index'  # Special case for root route
    elif '.' not in endpoint:
        endpoint = f'main.{endpoint}'  # Add main blueprint prefix if no blueprint specified

    # Replace hyphens with underscores in endpoint names
    endpoint = endpoint.replace('-', '_')
    
    # Verify the endpoint exists
    actual_endpoint = get_actual_endpoint(endpoint)
    _route_cache[route] = actual_endpoint
    
    return actual_endpoint

def map_route_to_roles(route_path, page_name, roles=None, category_id=None, icon='fa-link', weight=0):
    """Map a route to specific roles and create/update the PageRouteMapping."""
    try:
        # Convert route_path to actual endpoint
        endpoint = route_to_endpoint(route_path)
        
        # Get or create the route mapping
        mapping = PageRouteMapping.query.filter_by(route=endpoint).first()
        if not mapping:
            mapping = PageRouteMapping(
                route=endpoint,
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
        
        # If no roles specified, grant access to all roles by default
        if roles is None:
            roles = ['admin', 'demo']
        
        # Add role associations
        for role_name in roles:
            role = Role.query.filter_by(name=role_name).first()
            if role:
                mapping.allowed_roles.append(role)
            else:
                logger.warning(f"Role '{role_name}' not found when mapping route '{endpoint}'")
        
        db.session.commit()
        logger.info(f"Successfully mapped route '{endpoint}' to roles: {roles}")
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
        mapping = PageRouteMapping.query.filter_by(route=endpoint).first()
        
        # If no mapping exists, return default roles (all roles have access)
        if not mapping:
            return ['admin', 'demo']
            
        return [role.name for role in mapping.allowed_roles]
        
    except Exception as e:
        logger.error(f"Error getting roles for route '{route_path}': {str(e)}")
        return ['admin', 'demo']  # Default to all roles having access

def remove_route_mapping(route_path):
    """Remove a route mapping and its role associations."""
    try:
        # Convert route_path to actual endpoint
        endpoint = route_to_endpoint(route_path)
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
            roles=mapping.get('roles'),  # If not specified, will default to all roles
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
        new_routes = {route_to_endpoint(mapping['route']) for mapping in route_mappings}
        
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
