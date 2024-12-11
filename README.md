# Black Friday Lunch - Flask Application

A Flask-based enterprise application for managing operations, documentation, and team collaboration.

## Quick Start

1. Set up environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. Configure:
```bash
cp .env.example .env
# Edit .env with your settings
```

3. Initialize database:
```bash
flask db upgrade
python init_db.py
```

4. Run:
```bash
flask run
```

## Features

- **Document Management**: Knowledge base and documentation system
- **Project Management**: Track and manage projects and tasks
- **Dispatch Operations**: Handle operational dispatches
- **Handoffs**: Manage team handoffs and transitions
- **On-call Management**: Schedule and manage on-call rotations
- **User Profiles**: User management with LDAP integration
- **Admin Tools**: Administrative functions and system settings
- **Reporting**: Generate and view operational reports

## Project Structure

```
app/
├── plugins/          # Plugin modules (documents, projects, etc.)
├── static/          # Static assets and files
├── templates/       # HTML templates
├── utils/          # Utility functions and helpers
└── extensions.py   # Flask extensions
```

## Development

- Python 3.8+
- Flask web framework
- MariaDB/MySQL database
- Bootstrap frontend
- Plugin-based architecture

## Documentation

Detailed documentation is available through the application's document management system:

1. Log into the application
2. Navigate to Documents section
3. Filter by "System Documentation" category

Key documentation includes:
- Setup Guide: Detailed installation instructions
- Contributing Guidelines: Development standards and workflow
- API Documentation: Available endpoints and usage

## Testing

```bash
python -m pytest
```

## License

Proprietary - All rights reserved

## Support

For issues and support:
1. Check the in-app documentation
2. Contact system administrator
3. Submit bug reports through the project management system
