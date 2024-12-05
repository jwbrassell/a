# Blueprint Development Guide

## Overview
This guide outlines best practices for developing and integrating new blueprints into our Flask application, which supports multiple teams and a large user base with role-based access control (RBAC).

## Blueprint Structure
```
app/
└── your_blueprint/
    ├── __init__.py
    ├── routes.py
    ├── forms.py (if needed)
    ├── models.py (if needed)
    ├── README.md
    └── templates/
        └── your_blueprint/
            └── *.html
```

## Implementation Steps

### 1. Blueprint Setup

#### __init__.py
```python
from flask import Blueprint

bp = Blueprint('your_blueprint', __name__)

from app.your_blueprint import routes
```

#### routes.py
```python
from flask import render_template
from flask_login import login_required, current_user
from app.your_blueprint import bp
from app.utils.activity_tracking import track_activity
from app.utils.rbac import role_required
from app.utils.logging import log_info, log_error
from app.utils.route_manager import register_route

@bp.route('/example')
@login_required  # Always require login
@role_required(['required_role'])  # Always check roles
@track_activity  # Always track activity
@register_route  # Register route for validation
def example():
    try:
        log_info(f"User {current_user.name} accessed example page")
        return render_template('your_blueprint/example.html')
    except Exception as e:
        log_error(f"Error in example route: {str(e)}")
        flash('An error occurred', 'error')
        return redirect(url_for('main.index'))
```

### 2. Route Management

#### Route Registration
All routes must be properly registered using the route_manager:

```python
from app.utils.route_manager import register_route

@bp.route('/your-route')
@register_route  # Always include this decorator
def your_route():
    pass
```

#### Route Validation
Routes are automatically validated against database entries. To ensure proper validation:

1. Use consistent naming conventions:
   - Use lowercase letters and hyphens for URLs
   - Use underscores for function names
   - Keep names descriptive and consistent

2. Handle route aliases properly:
```python
@bp.route('/main-route')
@bp.route('/alternate-route')  # Alias
@register_route
def main_route():
    pass
```

3. Run route validation after changes:
```bash
python validate_routes.py
```

#### Route Caching
The route manager implements caching for improved performance:

```python
from app.utils.route_manager import get_cached_route

def your_function():
    route = get_cached_route('route_name')
    # Use cached route
```

### 3. Required Security Features

#### CSRF Protection
All forms must include CSRF protection. This is automatically handled by Flask-WTF, but you must:

1. Include the CSRF token in all forms:
```html
<form method="POST">
    {{ form.csrf_token }}  <!-- Always include this -->
    <!-- form fields -->
</form>
```

2. For AJAX requests, include the CSRF token in headers:
```javascript
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", "{{ csrf_token() }}");
        }
    }
});
```

#### User Authentication
1. Always use @login_required decorator
2. Access current user with current_user (from flask_login)
3. Check user permissions before operations:
```python
@bp.route('/protected-action', methods=['POST'])
@login_required
@role_required(['admin'])
def protected_action():
    if not current_user.can_perform_action():
        log_warning(f"User {current_user.name} attempted unauthorized action")
        abort(403)
    # proceed with action
```

#### Logging
Always implement proper logging in your routes:

```python
from app.utils.logging import log_info, log_warning, log_error

@bp.route('/important-action', methods=['POST'])
@login_required
def important_action():
    try:
        # Log the start of the action
        log_info(f"User {current_user.name} started important action")
        
        # Perform the action
        result = perform_action()
        
        # Log success
        log_info(f"User {current_user.name} completed important action: {result}")
        return jsonify({'success': True})
        
    except Exception as e:
        # Log errors
        log_error(f"Error in important_action: {str(e)}", exc_info=True)
        return jsonify({'error': 'An error occurred'}), 500
```

### 4. Template Integration

#### Base Template Extension
Always extend the base template and implement proper breadcrumbs:
```html
{% extends 'base.html' %}

{% block breadcrumb %}
<a href="{{ url_for('main.index') }}">Home</a>
<span class="separator">/</span>
<a href="{{ url_for('your_blueprint.index') }}">Your Section</a>
<span class="separator">/</span>
<span class="current">Current Page</span>
{% endblock %}

{% block content %}
<div class="container-fluid">
    <!-- Your content here -->
</div>
{% endblock %}
```

#### Route URL Generation
Always use the route manager's template filter for URL generation:
```html
<a href="{{ 'your_blueprint.route_name'|get_route }}">Link</a>
```

### 5. Role-Based Access Control

1. **Define Required Roles**
```python
from app.models import Role, PageRouteMapping
from app.utils.route_manager import register_route_mapping

def setup_blueprint_routes():
    # Create page route mapping
    new_route = PageRouteMapping(
        page_name='Your Feature',
        route='your_blueprint.route_name',
        category_id=category_id,
        icon='fa-appropriate-icon'
    )
    
    # Register route mapping
    register_route_mapping(new_route)
    
    # Assign allowed roles
    admin_role = Role.query.filter_by(name='admin').first()
    user_role = Role.query.filter_by(name='user').first()
    new_route.allowed_roles.extend([admin_role, user_role])
    
    db.session.add(new_route)
    db.session.commit()
```

2. **Check Roles in Routes**
```python
@bp.route('/admin-only')
@login_required
@role_required(['admin'])
@register_route
def admin_only():
    return render_template('your_blueprint/admin.html')
```

### 6. Activity Tracking

1. **Track User Actions**
The @track_activity decorator automatically logs:
- Page visits
- User actions
- Timestamps
- User information

2. **Custom Activity Tracking**
```python
from app.models import UserActivity

def track_custom_action(action_type, details):
    activity = UserActivity(
        user_id=current_user.id,
        action_type=action_type,
        details=details
    )
    db.session.add(activity)
    db.session.commit()
```

### 7. Error Handling

Always implement proper error handling:
```python
@bp.errorhandler(404)
def not_found_error(error):
    log_error(f"404 error: {request.url}")
    return render_template('404.html'), 404

@bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    log_error(f"500 error: {str(error)}", exc_info=True)
    return render_template('500.html'), 500
```

### 8. Testing Requirements

1. **Route Validation Tests**
```python
def test_route_validation():
    # Should validate route registration
    from app.utils.route_manager import validate_routes
    validation_result = validate_routes()
    assert validation_result.success
    assert len(validation_result.mismatches) == 0
```

2. **Authentication Tests**
```python
def test_login_required(client):
    # Should redirect to login
    response = client.get('/your-blueprint/protected')
    assert response.status_code == 302
    assert 'login' in response.location

    # Should succeed when logged in
    login(client, 'test@example.com', 'password')
    response = client.get('/your-blueprint/protected')
    assert response.status_code == 200
```

### 9. Documentation Requirements

1. **Blueprint README**
Your blueprint's README.md should include:
- Purpose and overview
- Setup instructions
- Required roles and permissions
- Route documentation
- API documentation
- Example usage

2. **Code Documentation**
```python
def your_function(param1: str, param2: int) -> bool:
    """
    Brief description of function.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        bool: Description of return value

    Raises:
        ValueError: Description of when this error occurs
    """
    pass
```

This guide will be updated as new requirements or best practices emerge. For questions or suggestions, please contact the development team.
