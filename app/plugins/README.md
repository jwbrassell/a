# Flask Plugin System Guide

This guide explains how to create and integrate new plugins into the Flask application.

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
from app.utils.rbac import role_required

bp = Blueprint('your_plugin', __name__,
              template_folder='templates',
              url_prefix='/your-plugin')

@bp.route('/')
@login_required
@role_required(['user'])
def index():
    return render_template('your_plugin/index.html',
                         metadata=plugin_metadata)
```

#### 3. Templates

Create templates extending the base template:

```html
{% extends 'base.html' %}

{% block title %}Your Plugin{% endblock %}

{% block breadcrumb %}
<ol class="breadcrumb">
    <li class="breadcrumb-item"><a href="{{ url_for('main.index') }}">Home</a></li>
    <li class="breadcrumb-item active">Your Plugin</li>
</ol>
{% endblock %}

{% block content %}
<!-- Your content here -->
{% endblock %}
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
- Use `@role_required([roles])` for authorization
- Define required roles in metadata

### Templates

- Always extend `base.html`
- Use proper breadcrumb navigation
- Follow Bootstrap component patterns
- Include plugin metadata display

### Static Files

If your plugin needs static files:

1. Create a `static` directory in your plugin
2. Reference files using:
```html
{{ url_for('your_plugin.static', filename='path/to/file') }}
```

## Best Practices

1. **Documentation**
   - Maintain a detailed README.md
   - Document all routes and features
   - Include setup instructions
   - List dependencies

2. **Security**
   - Always use authentication decorators
   - Implement proper role checks
   - Validate user input
   - Handle errors gracefully

3. **Code Organization**
   - Follow consistent naming
   - Keep routes organized
   - Use meaningful variable names
   - Comment complex logic

4. **UI/UX**
   - Follow Bootstrap patterns
   - Maintain consistent styling
   - Use proper icons
   - Implement responsive design

5. **Testing**
   - Write unit tests
   - Test role-based access
   - Verify template rendering
   - Check error handling

## Example Plugin

See the `hello` plugin for a complete example implementation:

```python
# app/plugins/hello/__init__.py
from flask import Blueprint, render_template
from flask_login import login_required
from app.utils.plugin_manager import PluginMetadata
from app.utils.rbac import role_required

bp = Blueprint('hello', __name__, 
              template_folder='templates',
              url_prefix='/hello')

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

@bp.route('/')
@login_required
@role_required(['user'])
def index():
    return render_template('hello/index.html', 
                         metadata=plugin_metadata)
```

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
```

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

3. **Access Issues**
   - Verify user roles
   - Check decorator order
   - Confirm URL prefix
   - Validate route registration

4. **Static Files**
   - Check file permissions
   - Verify path construction
   - Confirm static folder setup
   - Check URL generation
