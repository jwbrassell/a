# Project Plugin Improvements

## Tasks Table Improvements
1. Status and Priority Display
   - Fixed status and priority badges to properly display using task.status.color and task.priority.color
   - Added fallback for cases where status/priority is not set
   - Improved badge styling for better visibility

2. Task Actions
   - Changed onclick handlers to direct URL links for view/edit actions
   - Added proper route URLs using url_for()
   - Kept onclick handler for delete action to handle confirmation
   - Added data-task-id attributes for better JavaScript interaction

3. Task Summary Display
   - Added proper truncation for task descriptions
   - Added title attribute for hover tooltip with full description
   - Improved rich text content display in table cells

## Todo List Improvements
1. Layout Changes
   - Moved "Add Todo" button to card footer for better visual hierarchy
   - Improved table styling with proper theme support
   - Added proper vertical alignment for all table cells

2. Theme Support
   - Added proper Bootstrap 5 theme variables
   - Ensured dark mode compatibility
   - Fixed form control styling in both themes

## Project Info Improvements
1. Status/Priority Display
   - Already properly implemented with:
     - Badge display in readonly mode
     - Select2 dropdown in edit mode
     - Proper color coding for both modes

## Implementation Notes

### Tasks Table Template
- Use url_for() for view/edit links
- Keep delete as onclick handler for confirmation
- Proper status/priority badge display
- Improved summary/description truncation

### Todo List Template
- Card footer placement for add button
- Proper theme variable usage
- Consistent styling with project theme

### Project Info
- Current implementation already handles status/priority display correctly
- No changes needed as it already shows:
  - Badges in readonly mode
  - Select2 dropdowns in edit mode
  - Proper color coding in both modes
