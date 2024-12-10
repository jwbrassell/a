# Profile Plugin

A Flask plugin for managing user profiles including avatar customization and theme preferences.

## Features

- Custom avatar upload with size and type validation
- Selection from predefined avatar gallery
- Theme preference management (light/dark mode)
- AJAX-based theme switching
- Automatic avatar directory creation
- Secure file handling
- Activity tracking integration
- User preference persistence
- Random default avatar assignment

## Installation

1. Copy the profile plugin folder to your Flask application's plugins directory
2. The plugin will be automatically discovered and loaded by the plugin manager
3. No additional environment variables are required
4. The plugin uses the core User model's preference system, so no additional migrations are needed

## Access

- Main interface: `/profile/`
  - Upload custom avatar
  - Select from default avatars
  - Toggle theme preference
  - View current profile settings

## Required Roles

The plugin is available to all authenticated users and does not require specific roles.

## Usage

### Managing Avatar

1. Access the profile page at `/profile/`
2. To upload custom avatar:
   - Click "Upload Avatar" button
   - Select an image file (PNG or JPG)
   - File must be under 1MB
   - Image will be automatically saved and displayed
3. To use default avatar:
   - Browse the gallery of default avatars
   - Click on desired avatar to select
   - Avatar will be immediately updated

### Managing Theme

1. Access the profile page at `/profile/`
2. Toggle between light and dark themes:
   - Using the theme switcher button
   - Changes are saved automatically
   - Preference persists across sessions

## Dependencies

The plugin uses the following components (already included in the base application):

- Flask-Login: Authentication
- Werkzeug: Secure filename handling
- Bootstrap 5: UI framework
- Font Awesome 5: Icons
- jQuery: AJAX theme updates

## File Structure

- Static files:
  - Custom avatars: `static/uploads/avatars/`
  - Default avatars: `static/images/`
  - Naming format: `avatar_[user_id]_[timestamp].[extension]`

## File Validation

- Supported formats: PNG, JPG, JPEG
- Maximum file size: 1MB
- Secure filename handling
- Automatic directory creation
- Unique filename generation

## Navigation

The plugin automatically adds:
- "Profile" link in the main navigation with user avatar display

## Activity Tracking

The plugin integrates with the application's activity tracking system:
- Logs avatar uploads and changes
- Tracks theme preference updates
- Records user interactions with profile settings

## Error Handling

The plugin includes comprehensive error handling:
- File size validation
- File type validation
- Secure file operations
- User-friendly error messages
- AJAX error responses

## Troubleshooting

1. If avatar upload fails:
   - Verify file size is under 1MB
   - Check file format (PNG/JPG only)
   - Ensure uploads directory is writable
   - Review error messages in flash notifications

2. If theme switching fails:
   - Check browser console for AJAX errors
   - Verify user is authenticated
   - Review server logs for detailed errors

3. For missing avatars:
   - Verify file paths in user preferences
   - Check uploads directory permissions
   - Ensure default avatars are present in images directory

4. For preference issues:
   - Verify user model is properly configured
   - Check database connectivity
   - Review user preference table entries
