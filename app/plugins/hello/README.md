# Hello Plugin

An example plugin demonstrating the Flask plugin system capabilities.

## Overview

This plugin serves as a template and reference implementation for creating new plugins. It demonstrates:

- Basic plugin structure
- Route definition and protection
- Template organization
- Metadata configuration
- Role-based access control

## Structure

```
hello/
├── __init__.py          # Plugin initialization and routes
├── README.md           # Plugin documentation
└── templates/          # Plugin templates
    └── hello/
        ├── index.html  # Main plugin page
        └── about.html  # Plugin information page
```

## Features

- Basic plugin pages (index and about)
- Role-based access control
- Plugin metadata display
- Bootstrap-based UI
- Integration with main navigation

## Configuration

The plugin is configured through the `plugin_metadata` object in `__init__.py`:

```python
plugin_metadata = PluginMetadata(
    name="Hello Plugin",
    version="1.0.0",
    description="An example plugin demonstrating the plugin system",
    author="System",
    required_roles=["user"],
    icon="fa-hand-wave",
    category="Examples",
    weight=100
)
```

### Metadata Fields

- `name`: Display name of the plugin
- `version`: Plugin version
- `description`: Brief description of the plugin
- `author`: Plugin author/maintainer
- `required_roles`: List of roles required to access the plugin
- `icon`: FontAwesome icon class
- `category`: Navigation category for grouping
- `weight`: Order within the category (lower numbers appear first)

## Routes

- `/hello/` - Main plugin page
- `/hello/about` - Plugin information page

## Required Roles

- `user`: Basic user access required

## Usage

1. Install the plugin:
   ```python
   # In your Flask app
   from app.plugins.hello import bp
   app.register_blueprint(bp)
   ```

2. Ensure users have the required roles:
   ```python
   user.roles.append(Role.query.filter_by(name='user').first())
   ```

3. Access the plugin at `/hello/`

## Development

To create a new plugin based on this template:

1. Copy the plugin structure
2. Update `plugin_metadata`
3. Modify routes and templates
4. Add plugin-specific functionality
5. Document in README.md

## Best Practices

1. Always extend base.html
2. Use proper breadcrumb navigation
3. Implement role-based access control
4. Document all features
5. Follow consistent naming conventions
6. Use Bootstrap components for UI
7. Handle errors appropriately

## Testing

```python
def test_plugin_access():
    # Test unauthorized access
    response = client.get('/hello/')
    assert response.status_code == 302  # Redirects to login

    # Test authorized access
    login(client, 'test@example.com', 'password')
    response = client.get('/hello/')
    assert response.status_code == 200
