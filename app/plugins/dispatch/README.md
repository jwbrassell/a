# Dispatch Plugin

A Flask plugin for managing and tracking dispatch requests with email notifications.

## Features

- Create and send dispatch requests to teams
- Track dispatch transactions with priority levels
- Email notifications for new dispatch requests
- Admin interface for managing teams and priorities
- DataTables integration for viewing transactions
- Role-based access control
- Color-coded priorities with custom icons

## Installation

1. Copy the dispatch plugin folder to your Flask application's plugins directory
2. The plugin will be automatically discovered and loaded by the plugin manager
3. Configure your environment variables in `.env` file:

```bash
# Mail Configuration for Dispatch Plugin
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-email-password
MAIL_DEFAULT_SENDER=noreply@example.com
```

4. Run database migrations:

```bash
flask db migrate -m "Add dispatch plugin tables"
flask db upgrade
```

## Access

- Main interface: `/dispatch/`
  - Create new dispatch requests
  - View all transactions in DataTables
  - Track request status

- Management interface: `/dispatch/manage`
  - Configure teams and email addresses
  - Set up priorities with custom colors and icons
  - Accessible to users with admin role

## Required Roles

The plugin requires the following roles:
- `user`: Access to create and view dispatch requests
- `admin`: Access to manage teams and priorities

These roles will be automatically created if they don't exist.

## Usage

### Creating a Dispatch Request

1. Access the dispatch tool at `/dispatch/`
2. Click "New Dispatch" button
3. Fill out the form:
   - Select recipient team
   - Choose priority level
   - Enter description
   - Optionally add RMA information
   - Optionally add Bridge link
4. Submit to send email notification

### Managing Teams

1. Access `/dispatch/manage`
2. In the Teams section:
   - Click "Add Team" to create new team
   - Fill in team name, email, and description
   - Use edit button to modify existing teams

### Managing Priorities

1. Access `/dispatch/manage`
2. In the Priorities section:
   - Click "Add Priority" to create new priority
   - Set name, description, color, and icon
   - Use edit button to modify existing priorities

## Dependencies

The plugin uses the following components (already included in the base application):

- Flask-SQLAlchemy: Database models
- Flask-Login: Authentication
- DataTables: Transaction display
- Bootstrap 5: UI framework
- Font Awesome 5: Icons
- Bootstrap Colorpicker: Priority color selection

## Database Models

- DispatchTeam
  - name: Team name
  - email: Team email address
  - description: Optional team description

- DispatchPriority
  - name: Priority level name
  - description: Priority description
  - color: Hex color code
  - icon: Font Awesome icon class

- DispatchTransaction
  - team_id: Reference to team
  - priority_id: Reference to priority
  - description: Request description
  - is_rma: RMA flag
  - rma_info: RMA details
  - is_bridge: Bridge flag
  - bridge_link: Bridge URL
  - status: Request status
  - created_by_id: User reference
  - created_at: Timestamp

## Navigation

The plugin automatically adds:
- "Dispatch" link in the main navigation
- "Dispatch Settings" link in the Admin section

## Email Templates

Dispatch notifications include:
- Team information
- Priority level
- Description
- Requestor details
- Optional RMA information
- Optional Bridge link

## Troubleshooting

1. If emails are not sending:
   - Verify SMTP settings in .env file
   - Check mail server connectivity
   - Review error logs for specific issues

2. If access is denied:
   - Ensure user has required roles
   - Check role assignments in admin interface

3. For database issues:
   - Verify migrations are up to date
   - Check database connectivity
   - Review logs for SQL errors
