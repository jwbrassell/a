# Hello Plugin

An example plugin demonstrating the Flask plugin system functionality.

## Features

- Displays plugin metadata and configuration
- Demonstrates plugin routing system
- Shows role-based access control
- Integrates activity tracking
- Uses Bootstrap UI components
- Implements FontAwesome icons
- Demonstrates breadcrumb navigation
- Shows plugin information display

## Installation

1. Copy the hello plugin folder to your Flask application's plugins directory
2. The plugin will be automatically discovered and loaded by the plugin manager
3. No additional environment variables are required
4. No database migrations needed

## Access

- Main interface: `/hello/`
  - View plugin metadata
  - See configuration details
  - Access role information
  
- About page: `/hello/about`
  - Detailed plugin information
  - Complete configuration display
  - System integration details

## Required Roles

The plugin requires the following role:
- `user`: Basic access to view plugin pages

## Usage

### Main Page

1. Access the plugin at `/hello/`
2. View basic plugin information:
   - Version number
   - Author details
   - Category
   - Required roles
3. Navigate to About page for more details

### About Page

1. Access the about page at `/hello/about`
2. View comprehensive plugin details:
   - Plugin metadata
   - Configuration settings
   - Navigation weight
   - Icon information
   - Role requirements

## Dependencies

The plugin uses the following components (already included in the base application):

- Flask-Login: Authentication
- Bootstrap 5: UI framework
- Font Awesome 5: Icons
- Flask Blueprint: Route management

## Navigation

The plugin automatically adds:
- "Hello Plugin" link in the Examples category of main navigation
- Uses weight=100 for navigation ordering
- Includes FontAwesome icon display

## Activity Tracking

The plugin integrates with the application's activity tracking system:
- Logs access to main plugin page
- Tracks visits to about page
- Uses @track_activity decorator

## File Structure

```
hello/
├── __init__.py          # Plugin initialization and routes
├── README.md           # Plugin documentation
└── templates/          # HTML templates
    └── hello/
        ├── index.html  # Main plugin page
        └── about.html  # About page
```

## Error Handling

The plugin includes standard error handling:
- Authentication verification
- Role requirement checking
- Template rendering protection
- Standard Flask error pages

## Troubleshooting

1. If access is denied:
   - Verify user is authenticated
   - Check user has 'user' role
   - Ensure proper login

2. If navigation link is missing:
   - Check plugin loading in logs
   - Verify plugin_metadata configuration
   - Review navigation weight setting

3. For template issues:
   - Ensure templates are in correct directory
   - Check template inheritance
   - Verify base.html accessibility
