# Enhanced RBAC Implementation Guide

This guide provides step-by-step instructions for implementing the enhanced Role-Based Access Control (RBAC) system.

## Overview of Changes

1. New Models:
   - Enhanced Role model with hierarchy support
   - Permission model for granular access control
   - Action model for HTTP method-based permissions
   - RoutePermission for mapping routes to permissions

2. Database Migrations:
   - Add role hierarchy support
   - Create new permission-related tables
   - Initialize default data

3. Enhanced RBAC Utilities:
   - New permission checking functions
   - Role hierarchy management
   - Migration utilities

## Implementation Steps

### 1. Backup Current Data
```bash
# Create a database backup
pg_dump your_database_name > backup_before_rbac_enhancement.sql
```

### 2. Apply Database Migrations
```bash
# Run the migrations
flask db upgrade add_enhanced_rbac
flask db upgrade init_enhanced_rbac_data
```

### 3. Run Migration Script
```bash
# Run the migration script
python scripts/migrate_to_enhanced_rbac.py
```

### 4. Update Route Decorators

Replace existing `@requires_roles` decorators with the new permission-based decorators:

Old code:
```python
@bp.route('/example')
@requires_roles('admin', 'manager')
def example_route():
    return 'Example'
```

New code:
```python
@bp.route('/example')
@requires_permission('example_route_access', 'read')
def example_route():
    return 'Example'
```

### 5. Update Role Management

Use the new role hierarchy features in the admin interface:

```python
# Example: Setting up role hierarchy
def setup_roles():
    admin = Role.query.filter_by(name='admin').first()
    manager = Role.query.filter_by(name='manager').first()
    user = Role.query.filter_by(name='user').first()
    
    manager.parent = admin
    user.parent = manager
    db.session.commit()
```

### 6. Verify Implementation

1. Check Role Hierarchy:
```python
# Verify role relationships
admin = Role.query.filter_by(name='admin').first()
print(admin.get_descendants())  # Should show all child roles
```

2. Test Permissions:
```python
# Verify permission assignments
user_role = Role.query.filter_by(name='user').first()
print(user_role.get_permissions(include_parent=True))  # Should include inherited permissions
```

3. Verify Route Access:
```python
# Test route access with new permissions
permission = Permission.query.filter_by(name='example_route_access').first()
print(current_user.roles[0].has_permission(permission))
```

## Rollback Plan

If issues are encountered, you can rollback the changes:

1. Using the migration script:
```bash
python scripts/migrate_to_enhanced_rbac.py --rollback
```

2. Using database migrations:
```bash
flask db downgrade init_enhanced_rbac_data
flask db downgrade add_enhanced_rbac
```

3. Restore from backup if needed:
```bash
psql your_database_name < backup_before_rbac_enhancement.sql
```

## Testing the Implementation

### 1. Role Hierarchy Tests
```python
def test_role_hierarchy():
    # Create test roles
    admin = Role(name='test_admin', created_by='system')
    manager = Role(name='test_manager', created_by='system')
    user = Role(name='test_user', created_by='system')
    
    # Set up hierarchy
    manager.parent = admin
    user.parent = manager
    
    # Verify hierarchy
    assert user.get_hierarchy_level() == 2
    assert manager.get_hierarchy_level() == 1
    assert admin.get_hierarchy_level() == 0
    
    # Verify relationships
    assert admin.is_ancestor_of(user)
    assert user.is_descendant_of(admin)
```

### 2. Permission Tests
```python
def test_permissions():
    # Create test permission
    permission = Permission(
        name='test_permission',
        description='Test permission',
        created_by='system'
    )
    
    # Create test action
    action = Action(
        name='read',
        method='GET',
        created_by='system'
    )
    
    # Associate action with permission
    permission.actions.append(action)
    
    # Verify permission-action relationship
    assert action in permission.actions
```

### 3. Access Control Tests
```python
def test_access_control():
    # Create test route
    @app.route('/test')
    @requires_permission('test_permission', 'read')
    def test_route():
        return 'Test'
    
    # Test with unauthorized user
    response = client.get('/test')
    assert response.status_code == 403
    
    # Test with authorized user
    login_user(admin_user)
    response = client.get('/test')
    assert response.status_code == 200
```

## Monitoring and Maintenance

### 1. Monitor Permission Usage
```python
# Add logging to permission checks
logger.info(f"Permission check: {permission_name} for user {current_user.username}")
```

### 2. Regular Cleanup
```python
# Remove unused permissions
def cleanup_permissions():
    unused_permissions = Permission.query.filter(
        ~Permission.roles.any()
    ).all()
    for permission in unused_permissions:
        db.session.delete(permission)
    db.session.commit()
```

### 3. Audit Logging
```python
# Add audit log entries for permission changes
def log_permission_change(permission, action):
    audit_log = AuditLog(
        user_id=current_user.id,
        action=action,
        resource_type='permission',
        resource_id=permission.id
    )
    db.session.add(audit_log)
```

## Best Practices

1. **Permission Naming**
   - Use descriptive names: `manage_users`, `view_reports`
   - Follow consistent naming pattern: `<action>_<resource>`
   - Document permission purposes

2. **Role Hierarchy**
   - Keep hierarchy depth reasonable (3-4 levels max)
   - Document role relationships
   - Regularly review hierarchy structure

3. **Performance**
   - Cache permission checks where appropriate
   - Use eager loading for role/permission relationships
   - Index frequently queried columns

4. **Security**
   - Regularly audit permission assignments
   - Remove unused permissions
   - Log permission changes
   - Validate role hierarchy changes

## Troubleshooting

### Common Issues and Solutions

1. **Circular Role Dependencies**
   - Symptom: Infinite loops in permission checks
   - Solution: Verify role hierarchy using `verify_role_hierarchy()`

2. **Missing Permissions**
   - Symptom: Unexpected access denials
   - Solution: Check permission migration logs and run verification

3. **Performance Issues**
   - Symptom: Slow permission checks
   - Solution: Add caching and optimize queries

### Debug Tools

1. **Permission Debugging**
```python
def debug_user_permissions(user):
    """Print detailed permission information for a user."""
    print(f"User: {user.username}")
    for role in user.roles:
        print(f"\nRole: {role.name}")
        print("Permissions:")
        for permission in role.get_permissions():
            print(f"  - {permission.name}")
            print("    Actions:")
            for action in permission.actions:
                print(f"      * {action.name} ({action.method})")
```

2. **Role Hierarchy Visualization**
```python
def print_role_tree(role, level=0):
    """Print role hierarchy as a tree."""
    print("  " * level + f"- {role.name}")
    for child in role.children:
        print_role_tree(child, level + 1)
```

## Support and Maintenance

1. Regular maintenance tasks:
   - Review and clean up unused permissions
   - Audit role hierarchies
   - Update permission documentation
   - Monitor performance metrics

2. Keep documentation updated:
   - Maintain list of permissions and their purposes
   - Document role hierarchy changes
   - Update implementation guides

3. Monitor system health:
   - Track permission check performance
   - Monitor authorization failures
   - Review audit logs

## Future Enhancements

1. Consider implementing:
   - Permission groups for easier management
   - Time-based permissions
   - Context-aware permissions
   - Permission templates

2. Potential optimizations:
   - Permission check caching
   - Batch permission updates
   - Optimized hierarchy traversal

Remember to maintain backward compatibility and provide migration paths for any future enhancements.
