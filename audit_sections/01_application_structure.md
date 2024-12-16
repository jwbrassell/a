# Section 1: Application Structure

## 1.1 Directory Structure
```
app/
├── __init__.py          # Application factory
├── extensions.py        # Flask extensions
├── forms.py            # Form definitions
├── logging_utils.py    # Logging configuration
├── mock_ldap.py        # LDAP mock for development
├── template_filters.py  # Custom template filters
```

## 1.2 Core Components

### 1.2.1 Models (/app/models/)
- User Management:
  - user.py: User model
  - role.py: Role definitions
  - permission.py/permissions.py: Permission system
- Analytics & Tracking:
  - activity.py: Activity tracking
  - analytics.py: Analytics data
  - metrics.py: System metrics
- Content:
  - documents.py: Document management
  - navigation.py: Navigation structure

### 1.2.2 Routes (/app/routes/)
- Core Routes:
  - routes.py: Main application routes
- Admin Routes:
  - admin/routes.py: Admin panel
  - admin/api.py: Admin API endpoints
  - admin/api_analytics.py: Analytics API
  - admin/api_roles.py: Role management
  - admin/monitoring.py: System monitoring
- Document Management:
  - documents/routes.py: Document handling
  - documents/forms.py: Document forms
  - documents/utils.py: Document utilities
- User Profile:
  - profile/routes.py: User profile management

### 1.2.3 Utils (/app/utils/)
- Security:
  - rbac.py: Role-based access control
  - enhanced_rbac.py: Enhanced RBAC features
  - vault_security_monitor.py: Vault security
- System:
  - cache_manager.py: Caching system
  - metrics_collector.py: Metrics collection
  - request_tracking.py: Request monitoring
- Plugin System:
  - plugin_base.py: Plugin architecture base
  - plugin_manager.py: Plugin management
- Navigation:
  - navigation_manager.py: Navigation handling
  - route_manager.py: Route management
- Analytics:
  - activity_tracking.py: User activity tracking
  - analytics_service.py: Analytics services

## 1.3 Static Assets
- CSS Frameworks:
  - Bootstrap
  - AdminLTE
- JavaScript Libraries:
  - jQuery
  - DataTables
  - Highcharts
  - TinyMCE
- Custom Assets:
  - src/css/theme.css
  - src/js/admin/*
  - images/*

## 1.4 Templates
- Base Templates:
  - base.html: Main layout
  - error_base.html: Error page layout
- Error Pages:
  - 400.html, 403.html, 404.html, 500.html
- Admin Interface:
  - admin/*.html: Admin panel views
- Document Management:
  - documents/*.html: Document handling views
- User Interface:
  - profile.html: User profile
  - login.html: Authentication
  - index.html: Dashboard

## 1.5 Configuration Files
- config.py: Application configuration
- setup_*.py: Various setup scripts
- init_db.py: Database initialization
- gunicorn.conf.py: Gunicorn configuration
