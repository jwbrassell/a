# Plugin to Core Migration Plan

## Current Status (Updated)

### Core Components (✓ Completed)
1. Admin Plugin (✓)
   - Models in app/models/
   - Routes in app/routes/admin/
   - Templates in app/templates/admin/
   - Status: Fully migrated

2. Profile Plugin (✓)
   - Models in app/models/
   - Routes in app/routes/profile/
   - Templates in app/templates/profile/
   - Status: Fully migrated

3. Documents Plugin (✓)
   - Models in app/models/documents.py
   - Routes in app/routes/documents/
   - Templates in app/templates/documents/
   - Status: Fully migrated

4. Handoffs Plugin (✓)
   - Current: app/plugins/handoffs/
   - Status: Standardization completed
   - Dependencies: User system, Teams
   - Completed steps:
     - ✓ Implemented PluginBase
     - ✓ Standardized structure
     - ✓ Updated routes with error handling
     - ✓ Added comprehensive unit tests
     - ✓ Updated documentation

5. Dispatch Plugin (✓)
   - Current: app/plugins/dispatch/
   - Status: Standardization completed
   - Dependencies: User system
   - Completed steps:
     - ✓ Implemented PluginBase
     - ✓ Organized email functionality
     - ✓ Improved error handling
     - ✓ Added proper configuration
     - ✓ Added form validation
     - ✓ Added unit tests
     - ✓ Updated documentation

6. Oncall Plugin (✓)
   - Current: app/plugins/oncall/
   - Status: Standardization completed
   - Dependencies: User system, Teams
   - Completed steps:
     - ✓ Implemented PluginBase
     - ✓ Added error handling and logging
     - ✓ Updated routes with standardization
     - ✓ Added comprehensive unit tests
     - ✓ Updated documentation

7. Projects Plugin (✓)
   - Current: app/plugins/projects/
   - Status: Standardization completed
   - Dependencies: User system, Documents
   - Completed steps:
     - ✓ Implemented PluginBase
     - ✓ Created modular route structure
     - ✓ Added error handling and logging
     - ✓ Added comprehensive unit tests
     - ✓ Added proper configuration

8. AWS Monitor Plugin (✓)
   - Current: app/plugins/awsmon/
   - Status: Standardization completed
   - Dependencies: Metrics system
   - Completed steps:
     - ✓ Implemented PluginBase
     - ✓ Split routes into logical modules
     - ✓ Added user tracking and soft delete
     - ✓ Standardized API responses
     - ✓ Added comprehensive unit tests
     - ✓ Created database migration

### Pending Plugins

9. Reports Plugin
   - Current: app/plugins/reports/
   - Status: Pending standardization
   - Dependencies: Analytics system
   - Next steps:
     - [ ] Implement PluginBase
     - [ ] Standardize structure

#### Low Priority
10. Tracking Plugin
    - Current: app/plugins/tracking/
    - Status: Pending evaluation for core consolidation
    - Next steps:
      - [ ] Evaluate core integration
      - [ ] If kept as plugin, implement PluginBase

11. Weblinks Plugin
    - Current: app/plugins/weblinks/
    - Status: Pending standardization
    - Next steps:
      - [ ] Implement PluginBase
      - [ ] Standardize structure

## Plugin Standard Requirements

### Required Structure
```
plugin_name/
├── __init__.py
│   └── PluginClass(PluginBase)
├── routes.py
├── models.py (if needed)
├── templates/
│   └── plugin_name/
└── static/
    └── plugin_name/
```

### Plugin Class Template
```python
from app.utils.plugin_base import PluginBase, PluginMetadata
from flask import Blueprint

class PluginNamePlugin(PluginBase):
    def __init__(self):
        metadata = PluginMetadata(
            name="plugin_name",
            version="1.0.0",
            description="Plugin description",
            author="Author name",
            required_roles=[],
            icon="fa-icon-name",
            category="Category",
            weight=0
        )
        super().__init__(metadata)
        
        self.blueprint = Blueprint(
            'plugin_name',
            __name__,
            template_folder='templates',
            url_prefix='/plugin-path'
        )

    def init_app(self, app):
        super().init_app(app)
        from . import routes
```

## Next Actions

1. Reports Plugin (Next Focus)
   - [ ] Review current implementation
   - [ ] Plan standardization
   - [ ] Begin implementation

2. Tracking Plugin (Pending Evaluation)
   - [ ] Review current functionality
   - [ ] Evaluate core integration potential

## Progress Tracking

- ✓ = Completed
- 🔄 = In Progress
- ❌ = Not Started

Core Components:
- Admin ✓
- Profile ✓
- Documents ✓
- Handoffs ✓
- Dispatch ✓
- Oncall ✓
- Projects ✓
- AWS Monitor ✓

Monitoring & Reporting:
- Reports ❌

Utilities:
- Tracking ❌
- Weblinks ❌

## Testing Requirements

For each migration/standardization:
1. Unit tests for plugin functionality
2. Integration tests with core
3. Permission verification
4. Route accessibility tests
5. Template rendering tests

## Documentation Updates

For each completed migration/standardization:
1. Update API documentation
2. Update user guides
3. Document configuration options
4. Update developer guides

## Rollback Procedures

1. Keep backup of plugin code
2. Document database state
3. Maintain old routes temporarily
4. Test rollback procedures

This plan will be updated as we progress through each plugin migration and standardization.
