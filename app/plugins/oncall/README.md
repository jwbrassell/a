# On-Call Rotation Plugin

## Overview
The On-Call Rotation plugin provides a centralized system for managing and displaying on-call schedules. It supports multiple teams, calendar-based visualization, and CSV-based schedule imports.

## Features

### Team Management
- Create and manage multiple on-call teams
- Assign custom colors to teams for visual distinction
- Configure team-specific settings and contact information

### Schedule Management
- Upload schedules via CSV format
- Support for weekly rotation schedules
- Fields include: week number, person name, phone number
- Year-based organization of schedules

### Calendar View
- Interactive calendar display of on-call rotations
- Color-coded by team
- Week-based visualization
- Current on-call person highlighted
- Timezone support (displays in America/Chicago)

### Export Capabilities
- Export schedules by team and year
- Supports both JSON and CSV formats
- Includes all schedule details and contact information

### Access Control
- Role-based access control (RBAC)
- Admin role: Full access to all features
- Demo role: View-only access to schedules

## Technical Details

### Routes
- `oncall.index`: Main calendar view
- `oncall.manage_teams`: Team management interface
- `oncall.upload_oncall`: Schedule upload interface
- `oncall.export_schedule`: Schedule export endpoint (API)

### Database Models
- `Team`: Stores team information and settings
- `OnCallRotation`: Stores individual rotation entries

### Navigation
- Organized under the "Operations" category
- Export functionality accessible through UI, not direct navigation

## Recent Updates

### Route Management Fix
- Resolved navigation issues with parameterized routes
- Properly categorized routes under Operations section
- Improved URL generation for routes requiring parameters
- Fixed template handling of export_schedule route

### Integration Improvements
- Better alignment with core application structure
- Consistent with dispatch plugin patterns
- Enhanced error handling and user feedback

## Usage

### Uploading Schedules
1. Navigate to "Upload Schedule" in the Operations menu
2. Select team and year
3. Upload CSV file with required fields:
   - week
   - name
   - phone

### Viewing Schedules
1. Access "On-Call Schedule" in the Operations menu
2. View current on-call person
3. Navigate calendar for full schedule
4. Filter by team if needed

### Exporting Data
1. Use the export functionality within the calendar view
2. Select team and year
3. Choose export format (JSON/CSV)

## Future Enhancements
- Email notifications for upcoming rotations
- Integration with messaging systems
- Mobile app support
- Schedule conflict detection
- Automated schedule generation
