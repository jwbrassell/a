# Weblinks Plugin

The Weblinks plugin provides a centralized system for managing and organizing web links within the application. It offers both a quick access grid view and a detailed table view of all links, with features for categorization, tagging, and easy access.

## Features

- Quick access grid view with 3-row scrollable display
- Comprehensive table view with sorting and filtering
- Category and tag organization
- CSV import/export functionality
- Statistical charts for link distribution
- Default and custom icon support

## Interface

### Quick Access
- Links are displayed in a grid layout, flowing left to right
- Maximum of 3 rows visible at a time with vertical scrolling
- Each link shows:
  - Icon (default or custom)
  - Name
  - Category
  - Associated tags

### All Links Table
- Detailed view of all links with advanced filtering
- Columns include:
  - Icon
  - Name (clickable link)
  - URL
  - Category
  - Tags
  - Notes
  - Creation date

## Usage

### Adding Links
1. Click "Add New Link" button
2. Fill in required fields:
   - URL
   - Friendly Name
3. Optional fields:
   - Category (select existing or create new)
   - Tags (select existing or create new)
   - Icon (choose from available icons or use default link icon)
   - Notes

### Managing Links
- Use category and tag filters to find specific links
- Export links to CSV for backup or sharing
- Import links from CSV for bulk addition
- View usage statistics in the collapsible charts section

## Technical Details

### Icons
- Default icon: `fa-link` (Font Awesome link icon)
- Custom icons: Selected from Font Awesome icon set
- Icons are consistently displayed in both grid and table views

### Data Management
- CSV Import Format:
  - url
  - friendly_name
  - category
  - tags (comma-separated)
  - notes
  - icon

### Security
- Access restricted to authenticated users
- CSRF protection on all forms
- Input validation and sanitization

## Best Practices

1. Use descriptive friendly names for better searchability
2. Organize links with categories and tags for easier filtering
3. Add notes to provide context or additional information
4. Use custom icons to visually distinguish different types of links
