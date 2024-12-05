# Flask Portal Application

## Overview
A Flask-based web application with role-based access control (RBAC), plugin system, comprehensive user activity tracking, and user preferences. Supports both LDAP and local authentication.

## Features
- **Authentication**
  - LDAP Authentication (using test123 as password)
  - Local Development Users:
    * admin:admin123 (admin role)
    * user:user123 (demo role)
  - Automatic redirection to login page for unauthenticated users
  - Post-login redirection to originally requested page

- **User Preferences**
  - Persistent user preferences storage
  - Dark/Light theme toggle
  - Theme preference synced across sessions
  - Extensible preferences system for plugins
  - Real-time theme switching without page reload

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
  - Example plugins included (admin, hello, profile)

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
  - Dark/Light mode support
  - Responsive design
  - Collapsible sidebar
  - Breadcrumb navigation
  - Flash messages
  - Loading animations

[Rest of README remains the same...]
