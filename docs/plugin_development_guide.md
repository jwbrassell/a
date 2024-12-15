# Plugin Development Guide

## Overview

This guide explains how to create plugins for the Flask application using our standardized plugin system. The system provides a consistent structure and common functionality while allowing flexibility in implementation.

## Plugin Structure

A standard plugin follows this directory structure:
```
app/plugins/your_plugin/
├── __init__.py           # Plugin initialization and main class
├── models.py             # Database models
├── routes.py            # Route handlers (optional)
├── static/              # Static files
│   ├── css/            # Plugin-specific styles
│   └── js/             # Plugin-specific scripts
└── templates/          # Plugin templates
    └── your_plugin/    # Plugin-specific templates
```

## Creating a New Plugin

1. Copy the template plugin:
```bash
cp -r app/plugins/template app/plugins/your_plugin_name
```

2. Update the plugin metadata in `__init__.py`:
```python
metadata = PluginMetadata(
    name='your_plugin_name',
    version='1.0.0',
    description='Your plugin description',
    author='Your Name',
    required_roles=['user'],
    icon='fas fa-your-icon',
    category='your-category',
    weight=100
)
```

## Plugin Base Features

### 1. Error Handling

The base plugin provides standardized error handling:
```python
@plugin_error_handler
def your_route():
    # Your code here
    pass
```

### 2. Logging

Built-in logging support:
```python
from app.utils.plugin_base import PluginBase

class YourPlugin(PluginBase):
    def some_method(self):
        self.logger.info("Something happened")
        self.log_action('custom_action', {'detail': 'value'})
```

### 3. Role-Based Access Control

Define required roles in metadata:
```python
required_roles=['admin', 'user']
```

### 4. Static Resource Management

Automatic static file handling:
```python
# In templates
<link rel="stylesheet" href="{{ url_for('your_plugin.static', filename='css/style.css') }}">
```

## Best Practices

### 1. Model Definition

Use the standard model pattern:
```python
from app.extensions import db

class YourModel(db.Model):
    __tablename__ = 'your_plugin_items'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @classmethod
    def create(cls, **kwargs):
        try:
            item = cls(**kwargs)
            db.session.add(item)
            db.session.commit()
            return item
        except SQLAlchemyError as e:
            db.session.rollback()
            raise
```

### 2. Route Organization

Use blueprint routing:
```python
@blueprint.route('/')
@login_required
def index():
    return render_template(
        plugin.get_template_path('index.html'),
        plugin_name=plugin.metadata.name
    )
```

### 3. Template Structure

Follow the template hierarchy:
```html
{% extends "base.html" %}

{% block content %}
<div class="container">
    <!-- Your content here -->
</div>
{% endblock %}

{% block scripts %}
{{ super() }}
<script src="{{ url_for('your_plugin.static', filename='js/your_plugin.js') }}"></script>
{% endblock %}
```

### 4. JavaScript Organization

Use modular JavaScript:
```javascript
class YourPlugin {
    constructor() {
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Your initialization code
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.yourPlugin = new YourPlugin();
});
```

## Security Considerations

1. Input Validation
```python
from flask import request
from werkzeug.utils import secure_filename

@blueprint.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    filename = secure_filename(file.filename)
    # Additional validation...
```

2. CSRF Protection
```python
# Automatically added to all forms via base template
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
```

3. Access Control
```python
from flask_login import login_required, current_user

@blueprint.route('/admin')
@login_required
def admin():
    if 'admin' not in current_user.roles:
        abort(403)
    return render_template(plugin.get_template_path('admin.html'))
```

## Performance Optimization

1. Use Caching
```python
from app.utils.cache_manager import cached

@blueprint.route('/data')
@cached(timeout=300)
def get_data():
    return expensive_operation()
```

2. Database Query Optimization
```python
# Use specific columns
items = Model.query.with_entities(Model.id, Model.name).all()

# Use joins efficiently
items = Model.query.join(OtherModel).filter(OtherModel.active == True).all()
```

## Testing

Create tests in `tests/plugins/your_plugin/`:
```python
def test_plugin_initialization(app):
    plugin = YourPlugin()
    plugin.init_app(app)
    assert plugin.blueprint is not None
    assert 'your_plugin' in app.blueprints

def test_plugin_routes(client):
    response = client.get('/your_plugin/')
    assert response.status_code == 200
```

## Troubleshooting

Common issues and solutions:

1. Plugin Not Loading
- Check plugin directory name matches metadata name
- Verify __init__.py creates plugin instance
- Check for syntax errors

2. Static Files Not Found
- Verify static directory structure
- Check file permissions
- Use correct url_for calls

3. Database Errors
- Run migrations
- Check model definitions
- Verify database connections

## Plugin Lifecycle

1. Initialization
```python
def __init__(self):
    super().__init__(metadata)
    self.init_blueprint()
    self.register_routes()
    self.register_models()
```

2. Registration
```python
def init_app(self, app):
    super().init_app(app)
    # Plugin-specific initialization
```

3. Cleanup
```python
def cleanup(self):
    # Cleanup resources
    pass
```

## API Documentation

Document your plugin's API:
```python
@blueprint.route('/api/data', methods=['GET'])
def get_data():
    """
    Get plugin data.
    
    Returns:
        JSON response with data
    
    Example:
        >>> response = client.get('/your_plugin/api/data')
        >>> response.json
        {'data': [...]}
    """
    pass
```

## Deployment Considerations

1. Static Files
- Use proper static file serving in production
- Consider CDN for large files
- Implement cache headers

2. Database
- Create proper indexes
- Implement migrations
- Consider connection pooling

3. Monitoring
- Implement health checks
- Add performance monitoring
- Set up error tracking

## Support and Resources

- Report issues in the issue tracker
- Contribute improvements via pull requests
- Join the developer community
- Check documentation updates
