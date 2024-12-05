# Release Notes

## Version 1.8
### Navigation Visibility Control
- Added ability to control route visibility in navigation bar:
  - New show/hide toggle in route management interface
  - Visual indicators showing route visibility status
  - Default visibility set to "shown" for existing routes
  - Routes remain accessible via direct URL when hidden
- Enhanced route management interface:
  - Added visibility column to routes table
  - Added eye/eye-slash icons for clear visibility status
  - Added Bootstrap custom switch for easy toggling
- Updated navigation system:
  - Navigation manager now respects visibility settings
  - Hidden routes excluded from navigation bar
  - Breadcrumb navigation still works for hidden routes
- Database changes:
  - Added show_in_navbar boolean column to route mappings
  - Added migration with safe SQLite compatibility
  - Existing routes automatically set to visible

## Version 1.7
### Route Handling System Overhaul
- Implemented comprehensive route validation system (validate_routes.py):
  - Automated scanning of registered Flask routes
  - Database entry comparison and validation
  - Mismatch detection and correction
  - Detailed validation reporting
- Enhanced Route Manager improvements (route_manager.py):
  - Added route caching for improved performance
  - Implemented comprehensive route alias handling
  - Added automatic endpoint conversion
  - Enhanced error handling for route mismatches
  - Added special case handling for known route variations
- Template Integration:
  - Enhanced template filter for consistent route conversion
  - Improved endpoint lookup reliability in templates
- Validation Results:
  - Successfully validated all 46 routes
  - Eliminated route mismatches
  - Ensured consistency between Flask endpoints and database entries

## Version 1.6
### Documents Module Enhancements
- Added dynamic search functionality with real-time updates
- Implemented category filtering with instant results
- Enhanced document cards with improved visual layout:
  - Added thumbnail previews for image attachments
  - Added file type indicators for non-image attachments
  - Improved tag display with badge styling
  - Added last update timestamp and author information
- Added image modal for full-size preview of document images
- Improved empty state handling with clear user guidance
- Added AJAX-powered search to prevent page reloads
- Enhanced file upload handling:
  - Added secure filename processing
  - Implemented file size validation (20MB limit)
  - Added support for multiple file types (png, jpg, jpeg, gif, pdf, doc, docx)
- Improved form validations:
  - Added length constraints for document titles (1-256 characters)
  - Added length constraints for category names (1-128 characters)
  - Added length constraints for tag names (1-64 characters)
  - Added validation for search query length (max 100 characters)
  - Added descriptive error messages for all validations

## Version 1.5
### Site-wide Navigation Improvements
- Added consistent breadcrumb navigation across entire application
- Implemented hierarchical navigation structure:
  - Home page shows simplified "Home" breadcrumb
  - Top-level sections show "Home / Section Name"
  - Sub-pages show "Home / Section / Page Name"
  - Document pages show dynamic titles
- Added breadcrumbs to all major sections:
  - Admin section
  - Documents section
  - About section
  - User profile
  - Database summary
- Enhanced user orientation with clear location context
- Improved navigation paths throughout application

## Version 1.4
### Database Summary Improvements
- Added breadcrumb navigation for improved user orientation
- Fixed table details modal functionality with Bootstrap 5 compatibility
- Enhanced UI with interactive data visualizations:
  - Added pie chart for table size distribution
  - Added column chart for row count distribution
- Improved database overview with key metrics display
- Added comprehensive table details view with:
  - Column definitions
  - Index information
  - Recent entries sample

## Version 1.3
### Handoffs Module Enhancements
- Replaced daterangepicker with native HTML5 datetime picker
- Added 15-minute step intervals for more precise time selection
- Implemented 24-hour time format for consistency
- Fixed modal display issues with improved z-index handling
- Enhanced calendar icon interaction
- Optimized date format handling for form submissions
- Improved shift assignment handling in handoff creation
- Added robust error handling for handoff operations
- Enhanced form validation with proper length constraints
- Added clear placeholder text for better user guidance

### Navigation Order Management
- Added new admin page for managing navigation order
- Added drag and drop functionality to reorder navigation items
- Added ability to reorder both individual links and category groups
- Added side-by-side preview showing current vs new layout
- Added confirmation dialog before saving changes
- Added visual indentation for items under categories
- Added weight field to PageRouteMapping model to persist order

## Version 1.2
### Database Enhancements
- Added new tables for document management
- Added support for file uploads
- Added tags and categories for documents

### User Interface Updates
- Improved navigation sidebar
- Added admin dashboard
- Added document management interface
- Added user profile page
- Added LDAP authentication support

## Version 1.1
### Security Enhancements
- Added role-based access control
- Added user activity logging
- Added page visit tracking
- Added CSRF protection

## Version 1.0
### Initial Release
- Core system functionality
- Basic documentation including:
  - API documentation
  - Setup instructions
  - User management documentation
