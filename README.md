# Flask Portal Application

## Overview
A Flask-based web application with role-based access control (RBAC), supporting both LDAP and local authentication.

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
├── forms.py            # Form definitions
├── utils/              # Utility modules
│   ├── __init__.py
│   ├── route_manager.py # Route management and caching
│   ├── rbac.py         # Role-based access control
│   └── init_db.py      # Database initialization
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
