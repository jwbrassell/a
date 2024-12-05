# Role-Based Access Control (RBAC) System

This directory contains utilities for implementing Role-Based Access Control (RBAC) in the Flask application.

## Overview

The RBAC system provides:
- Centralized access control through route mappings
- Role-based authorization for all routes
- Easy-to-use decorators for protecting routes
- Utilities for managing route-role mappings

## Components

### 1. RBAC Core (rbac.py)
- `check_route_access()`: Middleware function to check route access
- `requires_roles()`: Decorator for role-based route protection
- `get_user_accessible_routes()`: Utility to get routes accessible to a user

### 2. Route Manager (route_manager.py)
- `map_route_to_roles()`: Map a route to specific roles
- `get_route_roles()`: Get roles associated with a route
- `remove_route_mapping()`: Remove a route mapping
- `bulk_update_route_mappings()`: Update multiple mappings at once
- `sync_blueprint_routes()`: Sync route mappings for a blueprint

## Usage

### Protecting Routes with Roles

```python
from app.utils.rbac import requires_roles

@app.route('/admin/dashboard')
@requires_roles('admin')
def admin_dashboard():
    return render_template('admin/dashboard.html')
```

### Managing Route Mappings

```python
from app.utils.route_manager import map_route_to_roles

# Map a route to roles
map_route_to_roles(
    route_path='/admin/dashboard',
    page_name='Admin Dashboard',
    roles=['admin'],
    category_id=1,
    icon='fa-dashboard',
    weight=0
)
```

### Syncing Blueprint Routes

```python
from app.utils.route_manager import sync_blueprint_routes

# Define route mappings
routes = [
    {
        'route': '/admin/dashboard',
        'page_name': 'Admin Dashboard',
        'roles': ['admin'],
        'category_id': 1,
        'icon': 'fa-dashboard',
        'weight': 0
    }
]

# Sync routes for blueprint
sync_blueprint_routes('admin', routes)
```

## Initial Setup

1. Run the setup script to create initial route mappings:
```bash
python setup_route_mappings.py
```

2. Use the route manager utilities to manage access control:
```python
from app.utils.route_manager import map_route_to_roles, get_route_roles

# Add new route mapping
map_route_to_roles('/new/route', 'New Page', ['admin', 'user'])

# Check route roles
roles = get_route_roles('/new/route')
```

## Models

The RBAC system uses the following database models:

1. `Role`: Represents user roles (admin, user, etc.)
2. `PageRouteMapping`: Maps routes to roles and navigation categories
3. `Category`: Organizes routes into navigation categories

## Best Practices

1. Always use the `@requires_roles` decorator for role-specific routes
2. Keep route mappings organized by blueprint
3. Use the route manager utilities instead of direct database manipulation
4. Regularly audit route mappings using `get_route_roles()`
5. Consider navigation organization when setting category_id and weight

## Security Considerations

1. Routes without mappings default to requiring authentication only
2. Multiple roles can be assigned to a single route
3. Users must have at least one matching role to access a route
4. Static files and error pages bypass RBAC checks
5. Failed access attempts are logged

## Troubleshooting

1. If a route is inaccessible:
   - Check the route mapping exists
   - Verify user has required role(s)
   - Check for typos in route paths
   - Review error logs for access denied entries

2. If navigation items are missing:
   - Verify route mappings exist
   - Check category assignments
   - Review role assignments
   - Verify weight values for ordering

3. If changes don't take effect:
   - Clear browser cache
   - Restart Flask application
   - Check database for correct mappings
   - Review error logs for any issues
