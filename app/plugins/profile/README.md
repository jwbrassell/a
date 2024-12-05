# Profile Plugin

A Flask plugin that adds user profile functionality to the portal application. This plugin provides a dedicated profile page accessible from both the top-right dropdown menu and the left sidebar navigation.

## Features

- View user profile information (name, email, roles)
- Accessible from two locations:
  - Top-right dropdown menu under the user's name
  - Left sidebar navigation above the logout button
- Requires only authentication (no specific role requirements)
- Follows the application's plugin architecture pattern

## Implementation Details

### Plugin Structure

```
profile/
├── __init__.py              # Plugin initialization, blueprint, and routes
├── README.md               # This documentation
└── templates/             # Template files
    └── profile/
        └── index.html     # Profile view template
```

### Blueprint Configuration

The plugin is implemented as a Flask Blueprint with the following configuration:

```python
bp = Blueprint('profile', __name__,
              template_folder='templates',
              static_folder='static',
              url_prefix='/profile')
```

### Plugin Metadata

The plugin uses the application's `PluginMetadata` class to define its characteristics:

```python
plugin_metadata = PluginMetadata(
    name="User Profile",
    version="1.0.0",
    description="User profile management plugin",
    author="System",
    required_roles=[],  # No specific roles required
    icon="fa-user",
    category="User",
    weight=98  # Positioned above logout
)
```

### Routes

The plugin provides a single route:

- `/profile/` - Main profile page
  - Requires authentication (@login_required)
  - Displays user information from current_user

### Template Integration

The plugin integrates with the base template through:

1. Conditional rendering in the top-right dropdown:
```html
{% if 'profile.index'|route_exists %}
<li>
    <a class="dropdown-item" href="{{ url_for('profile.index') }}">
        <i class="fas fa-user"></i> Profile
    </a>
</li>
{% endif %}
```

2. Conditional rendering in the left sidebar:
```html
{% if 'profile.index'|route_exists %}
<li class="nav-item">
    <a href="{{ url_for('profile.index') }}" class="nav-link">
        <i class="nav-icon fas fa-user"></i>
        <p>Profile</p>
    </a>
</li>
{% endif %}
```

### Template Filter

The plugin utilizes a custom template filter `route_exists` to handle conditional rendering:

```python
@app.template_filter('route_exists')
def route_exists(endpoint):
    """Check if a route exists in the application."""
    try:
        return endpoint in current_app.view_functions
    except:
        return False
```

## Installation

The plugin is automatically discovered and loaded by the application's plugin manager. No additional installation steps are required.

## Dependencies

- Flask-Login (for authentication)
- Application's plugin system (PluginMetadata, plugin manager)
- Bootstrap 5 (for UI components)
- Font Awesome (for icons)

## Security

- Access is restricted to authenticated users only
- No specific role requirements (accessible to all authenticated users)
- Uses the application's built-in authentication system

## Navigation

The plugin integrates into two navigation areas:

1. User dropdown menu (top-right)
   - Located under the user's name
   - Positioned above the logout option

2. Sidebar navigation (left)
   - Located in the bottom section
   - Positioned above the logout button
   - Weight set to 98 to ensure proper ordering

## Error Handling

- Uses conditional rendering to prevent template errors when the plugin is not loaded
- Gracefully handles cases where the plugin might be disabled or unregistered

## Future Enhancements

Potential future improvements could include:

- Profile editing functionality
- Profile picture upload
- Additional user information fields
- Activity history
- Security settings
