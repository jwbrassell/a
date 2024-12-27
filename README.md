# A-VaultIntegration

A Flask application that provides a robust web interface with Vault integration, role-based access control (RBAC), and various administrative features.

## Features

- **Vault Integration**: Secure secrets management and policy enforcement
- **Role-Based Access Control (RBAC)**: Fine-grained permission management with two primary roles:
  - Administrator: Full system access with all permissions
  - User: Standard access with basic read/write capabilities
- **Multiple Blueprints**:
  - AWS Manager: AWS resource management interface
  - Bug Reports: Issue tracking system
  - Database Reports: Database monitoring and reporting
  - Feature Requests: Feature request management
  - OnCall: On-call rotation management
  - Projects: Project management interface
  - Weblinks: Link management system

## Prerequisites

- Python 3.x
- HashiCorp Vault
- PostgreSQL (recommended)

## Installation

1. Clone the repository
2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy `.env.example` to `.env` and configure your environment variables:
```bash
cp .env.example .env
```

5. Initialize the database:
```bash
python init_database.py
```
This will create the default roles (Administrator and User) with appropriate permissions and set up initial route mappings.

## Vault Setup

1. Configure Vault using the provided configuration files in `config/`:
   - Development: `vault-dev.hcl`
   - Production: `vault-prod.hcl.template`
   - Secure Production: `vault-secure.hcl.template`

2. Initialize Vault and set up policies:
```bash
./scripts/setup_secure_vault.py
```

## Configuration

Key configuration files:
- `config.py`: Main application configuration
- `gunicorn.conf.py`: Gunicorn server configuration
- `.env`: Environment variables

## Role-Based Access Control

The application implements a two-tier role system:

### Administrator Role
- Full system access with all permissions
- Access to administrative features and configuration
- Can manage users, roles, and system settings
- Has access to all routes and features

### User Role
- Basic read/write access to standard features
- Limited to user-level operations
- Access to:
  - Document viewing and creation
  - Bug report submission
  - Feature request creation
  - Profile management

Permissions are enforced at multiple levels:
- Route level: Controls access to specific URLs
- Action level: Controls specific operations (read, write, update, delete)
- Feature level: Controls access to specific functionality

## Usage

### Development Server
```bash
python app.py
```

### Production Server
```bash
gunicorn -c gunicorn.conf.py wsgi:app
```

### System Service
A systemd service file is provided (`flask_app.service`) for running as a system service.

## Project Structure

```
.
├── app/
│   ├── blueprints/          # Feature modules
│   ├── models/              # Database models
│   ├── routes/              # Core route handlers
│   ├── static/              # Static assets
│   ├── templates/           # Jinja2 templates
│   └── utils/               # Utility functions
├── config/                  # Configuration files
├── scripts/                 # Management scripts
├── setup/                   # Setup documentation and scripts
└── vault/                   # Vault-related files
```

## Security

- All secrets are managed through Vault
- RBAC ensures proper access control through:
  - Standardized role definitions (Administrator/User)
  - Permission-based access control
  - Action-level granularity (read, write, update, delete)
  - Route-specific access mapping
- Request tracking and activity monitoring
- System health monitoring

## Contributing

1. Follow the Python style guide (PEP 8)
2. Write tests for new features
3. Update documentation as needed
4. Submit pull requests for review

## License

This project is proprietary and confidential.
