# Flask Portal Application

## Overview
A Flask-based web application with role-based access control (RBAC), plugin system, and comprehensive user activity tracking. Supports both LDAP and local authentication.

## Features
- **Authentication**
  - LDAP Authentication (using test123 as password)
  - Local Development Users:
    * admin:admin123 (admin role)
    * user:user123 (demo role)
  - Automatic redirection to login page for unauthenticated users
  - Post-login redirection to originally requested page

- **Authorization**
  - Role-Based Access Control (RBAC)
  - Default roles: admin and demo
  - Centralized access control through route mapping
  - Dynamic route permission checking
  - All routes accessible by default to both roles

- **Plugin System**
  - Modular architecture supporting dynamic plugin loading
  - Each plugin can have its own routes, templates, and static files
  - Automatic blueprint registration
  - Plugin-specific configuration and settings
  - Example plugins included (admin, hello)

- **Navigation System**
  - Hierarchical navigation with categories
  - Dynamic menu generation based on user roles
  - Customizable menu ordering
  - Icon support for menu items
  - Breadcrumb navigation

- **Activity Tracking**
  - Comprehensive user activity logging
  - Page visit tracking
  - Action tracking with timestamps
  - User session monitoring
  - Activity reports and analytics

- **UI/UX**
  - AdminLTE theme integration
  - Responsive design
  - Collapsible sidebar
  - Breadcrumb navigation
  - Flash messages
  - Loading animations

## Project Structure
```
app/
├── __init__.py          # Application factory and core setup
├── routes.py            # Main application routes
├── models.py            # Database models
├── forms.py             # Form definitions
├── logging_utils.py     # Logging configuration
├── mock_ldap.py         # LDAP authentication simulation
├── template_filters.py  # Custom template filters
├── plugins/            # Plugin system
│   ├── admin/          # Admin plugin for system management
│   │   ├── routes.py   # Admin routes
│   │   └── templates/  # Admin templates
│   └── hello/          # Example plugin
│       ├── routes.py   # Example routes
│       └── templates/  # Example templates
├── utils/              # Utility modules
│   ├── activity_tracking.py  # User activity tracking
│   ├── navigation_manager.py # Menu and navigation management
│   ├── plugin_manager.py    # Plugin system management
│   ├── rbac.py             # Role-based access control
│   ├── route_manager.py    # Route management and caching
│   └── init_db.py         # Database initialization
├── templates/          # HTML templates
│   ├── base.html       # Base template with AdminLTE theme
│   ├── index.html      # Main dashboard
│   ├── login.html      # Login page
│   └── error/          # Error pages (400, 403, 404, 500)
└── static/             # Static files (CSS, JS, images)
```

## Setup and Installation

### Prerequisites
- Python 3.8+
- pip
- Virtual environment (recommended)

### Installation Steps
1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-directory>
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Initialize the database:
```bash
flask db upgrade
```

6. Run the application:
```bash
flask run
```

## Authentication

### LDAP Authentication
- Uses mock LDAP for development
- All LDAP users use password: test123
- User information is automatically synchronized

### Local Development Users
Two default users are created for local development:
1. Admin User
   - Username: admin
   - Password: admin123
   - Role: admin

2. Demo User
   - Username: user
   - Password: user123
   - Role: demo

## Plugin System

### Overview
The application supports a plugin architecture that allows for modular extension of functionality:

1. Plugin Structure:
```
plugins/
└── your_plugin/
    ├── __init__.py      # Plugin initialization
    ├── routes.py        # Plugin routes
    ├── templates/       # Plugin templates
    └── README.md        # Plugin documentation
```

2. Plugin Registration:
- Plugins are automatically discovered and loaded
- Each plugin is registered as a Flask blueprint
- Plugin routes are automatically mapped to the navigation system

3. Available Plugins:
- **Admin Plugin**: System administration interface
  - User management
  - Role management
  - Route mapping
  - Category management
  - Activity logs
- **Hello Plugin**: Example plugin demonstrating basic functionality

## Navigation System

### Categories and Menu Structure
- Hierarchical navigation with categories
- Dynamic menu generation based on user roles
- Customizable menu ordering
- Support for icons and badges

### Navigation Management
```python
from app.utils.navigation_manager import create_category, add_route_to_category

# Create a new category
category = create_category("My Category", "fa-icon", order=1)

# Add route to category
add_route_to_category(route_path, category.id, "Page Name", "fa-page-icon")
```

## Activity Tracking

### Tracked Information
- Page visits
- User actions
- Login/logout events
- Error occurrences
- Administrative actions

### Usage
```python
from app.utils.activity_tracking import track_activity

@track_activity
def your_route():
    # Activity automatically tracked
    pass
```

## Utility Functions

### Route Management
- `register_route`: Register routes for validation
- `map_route_to_roles`: Map routes to specific roles
- `get_cached_route`: Get route information from cache

### RBAC Utilities
- `role_required`: Decorator for role-based access control
- `has_role`: Check if user has specific role
- `get_user_roles`: Get all roles for a user

### Logging Utilities
- `log_info`: Log informational messages
- `log_warning`: Log warning messages
- `log_error`: Log error messages with stack traces

### Vault Utility
- Secure credential storage
- Environment variable management
- Secret key rotation

## Route Access Control

### How It Works
1. When a user accesses a route:
   - System checks for route mapping in database
   - If no mapping exists, only authentication is required
   - If mapping exists but has no roles, only authentication is required
   - If mapping has roles, user must have at least one matching role

2. Access Control Flow:
   ```
   Request → Authentication Check → Route Mapping Check → Role Check → Access Granted/Denied
   ```

3. Default Configuration:
   - All routes are accessible to both admin and demo roles
   - Authentication is required for all non-public routes
   - Failed authentication redirects to login page
   - Successful login redirects to originally requested page

## Development Guide

### Adding New Routes
1. Create route in routes.py:
```python
@main.route('/new-route')
@login_required
@track_activity
def new_route():
    return render_template('new_route.html')
```

2. Create template in templates/:
```html
{% extends "base.html" %}
{% block content %}
    <!-- Your content here -->
{% endblock %}
```

### Adding Role Restrictions
1. Map route to roles:
```python
from app.utils.route_manager import map_route_to_roles

map_route_to_roles(
    route_path='/new-route',
    page_name='New Feature',
    roles=['admin'],  # Restrict to admin role
    icon='fa-new-icon'
)
```

### Error Handling
- 400: Bad Request
- 403: Forbidden
- 404: Not Found
- 500: Internal Server Error

All errors are logged and display user-friendly error pages.

## Blueprint Development
See [Blueprint Development Guide](app/BLUEPRINT_GUIDE.md) for detailed information about creating and integrating new blueprints.

## Contributing
1. Follow PEP 8 style guide
2. Write tests for new features
3. Update documentation
4. Submit pull request

## License
This project is licensed under the MIT License - see the LICENSE file for details.
