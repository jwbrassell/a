# Flask Plugin System Guide

This guide explains how to create, integrate, and safely remove plugins from the Flask application.

## Plugin Structure

A typical plugin follows this structure:

```
your_plugin/
├── __init__.py          # Plugin initialization and routes
├── README.md           # Plugin documentation
└── templates/          # Plugin templates
    └── your_plugin/
        ├── index.html  # Main plugin page
        └── about.html  # Plugin information page
```

## Creating a New Plugin

1. Create a new directory in `app/plugins/` with your plugin name
2. Create the basic structure as shown above
3. Implement the required components

### Required Components

#### 1. Plugin Metadata

In `__init__.py`, define your plugin metadata:

```python
from app.utils.plugin_manager import PluginMetadata

plugin_metadata = PluginMetadata(
    name="Your Plugin",
    version="1.0.0",
    description="Description of your plugin",
    author="Your Name",
    required_roles=["user"],
    icon="fa-your-icon",
    category="Your Category",
    weight=100
)
```

#### 2. Blueprint Definition

In `__init__.py`, create and configure your blueprint:

```python
from flask import Blueprint, render_template
from flask_login import login_required
from app.utils.rbac import requires_roles

bp = Blueprint('your_plugin', __name__,
              template_folder='templates',
              url_prefix='/your-plugin')

@bp.route('/')
@login_required
@requires_roles('user')
def index():
    return render_template('your_plugin/index.html',
                         metadata=plugin_metadata)
```

## Plugin Features

### Metadata Fields

- `name`: Display name in navigation and UI
- `version`: Plugin version number
- `description`: Brief description of functionality
- `author`: Plugin creator/maintainer
- `required_roles`: List of roles needed to access
- `icon`: FontAwesome icon class
- `category`: Navigation grouping category
- `weight`: Order within category (lower first)

### Access Control

- Use `@login_required` for authentication
- Use `@requires_roles([roles])` for authorization
- Define required roles in metadata

### Templates

- Always extend `base.html`
- Use proper breadcrumb navigation
- Follow Bootstrap component patterns
- Include plugin metadata display
- Use route validation filters for links

### Static Files

If your plugin needs static files:

1. Create a `static` directory in your plugin
2. Reference files using:
```html
{{ url_for('your_plugin.static', filename='path/to/file') }}
```

## Plugin Removal

When removing a plugin, the system will automatically:

1. Clean up invalid route mappings
2. Remove role associations
3. Update navigation structure
4. Handle URL generation gracefully

### Safe Removal Steps

1. Back up any important data
2. Remove the plugin directory
3. Restart the application
4. The system will automatically:
   - Clean up route mappings
   - Remove invalid role assignments
   - Update navigation
   - Handle missing endpoints gracefully

### Validation Checks

The system includes several safety mechanisms:

1. Route Validation:
   ```html
   {% if 'your_plugin.index'|route_exists %}
   <a href="{{ url_for('your_plugin.index') }}">Your Plugin</a>
   {% endif %}
   ```

2. Navigation Filtering:
   - Invalid routes are automatically filtered
   - Empty categories are hidden
   - Missing endpoints are handled gracefully

3. Error Handling:
   - Missing routes return 404
   - Invalid access returns 403
   - System errors show 500 page
   - All error pages work without navigation

## Best Practices

1. **Documentation**
   - Maintain a detailed README.md
   - Document all routes and features
   - Include setup instructions
   - List dependencies
   - Document removal procedures

2. **Security**
   - Always use authentication decorators
   - Implement proper role checks
   - Validate user input
   - Handle errors gracefully
   - Clean up data on removal

3. **Code Organization**
   - Follow consistent naming
   - Keep routes organized
   - Use meaningful variable names
   - Comment complex logic
   - Maintain clean uninstall

4. **UI/UX**
   - Follow Bootstrap patterns
   - Maintain consistent styling
   - Use proper icons
   - Implement responsive design
   - Handle missing routes gracefully

5. **Testing**
   - Write unit tests
   - Test role-based access
   - Verify template rendering
   - Check error handling
   - Test plugin removal

## Troubleshooting

1. **Plugin Not Appearing**
   - Check plugin directory name
   - Verify __init__.py exists
   - Confirm metadata is defined
   - Check required roles exist

2. **Template Errors**
   - Verify template directory structure
   - Check template inheritance
   - Validate template variables
   - Check URL generation
   - Use route validation filters

3. **Access Issues**
   - Verify user roles
   - Check decorator order
   - Confirm URL prefix
   - Validate route registration
   - Check role mappings

4. **Static Files**
   - Check file permissions
   - Verify path construction
   - Confirm static folder setup
   - Check URL generation

5. **Removal Issues**
   - Check for remaining route mappings
   - Verify role cleanup
   - Clear template cache
   - Restart application
   - Check error logs

## Integration Testing

Test your plugin integration:

```python
def test_plugin():
    # Test unauthorized access
    response = client.get('/your-plugin/')
    assert response.status_code == 302

    # Test authorized access
    login(client, 'user@example.com', 'password')
    response = client.get('/your-plugin/')
    assert response.status_code == 200
    assert 'Your Plugin' in response.data.decode()

    # Test plugin removal
    remove_plugin('your-plugin')
    response = client.get('/your-plugin/')
    assert response.status_code == 404  # Should handle missing route
