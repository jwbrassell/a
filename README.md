# Flask Black Friday Lunch Portal

A Flask-based web application for managing various aspects of development operations.

## Features

- Plugin-based architecture for extensibility
- Role-based access control
- Secure secret management with HashiCorp Vault
- CSRF protection
- Multiple plugin support
- Development tools and utilities

## Development Setup

### Prerequisites

- Python 3.8+
- HashiCorp Vault
- OpenSSL

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd flask-blackfridaylunch
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up development Vault server:
```bash
python setup_dev_vault.py
```

5. Copy example environment file and update with your settings:
```bash
cp .env.example .env
```

6. Initialize the database:
```bash
python init_db.py
```

### Development Vault Setup

The application uses HashiCorp Vault for secure secret management. For development:

1. Install HashiCorp Vault from https://developer.hashicorp.com/vault/downloads

2. Run the development setup script:
```bash
python setup_dev_vault.py
```

This will:
- Generate SSL certificates for HTTPS
- Initialize a development Vault server
- Configure the KV v2 secrets engine
- Create necessary access tokens

3. Update your .env file with the Vault credentials from .env.vault

### Security Notes

- The development Vault setup uses self-signed certificates
- HTTPS is enforced for all Vault communication
- Access is restricted to localhost only
- The web UI is disabled for security
- CSRF protection is enabled for all state-changing requests

### Plugin Development

When developing plugins that require secure credential storage:

1. Use the PluginCredentialManager from vault_utility.py:
```python
from vault_utility import VaultUtility

vault = VaultUtility()
credentials = vault.plugin_credentials.get_plugin_credentials("your-plugin-name")
```

2. Store plugin credentials:
```python
vault.plugin_credentials.store_plugin_credentials("your-plugin-name", {
    "api_key": "your-api-key",
    "secret": "your-secret"
})
```

3. Rotate credentials when needed:
```python
vault.plugin_credentials.rotate_plugin_credentials("your-plugin-name", new_credentials)
```

### CSRF Protection

The application includes built-in CSRF protection using Vault for token storage:

1. Generate a CSRF token:
```python
from vault_utility import VaultUtility

vault = VaultUtility()
token = vault.csrf.generate_token()
```

2. Use the csrf_protected decorator for routes:
```python
from vault_utility import csrf_protected

@app.route('/api/data', methods=['POST'])
@csrf_protected
def update_data():
    # Your route logic here
    pass
```

3. Include the token in requests:
```javascript
// In your frontend JavaScript
fetch('/api/data', {
    method: 'POST',
    headers: {
        'X-CSRF-Token': csrfToken,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify(data)
});
```

### Running the Application

1. Start the development server:
```bash
flask run
```

2. Access the application at http://localhost:5000

## Project Structure

```
.
├── app/                    # Application package
│   ├── plugins/           # Plugin modules
│   ├── templates/         # Jinja2 templates
│   ├── static/           # Static files
│   └── utils/            # Utility modules
├── config/               # Configuration files
│   └── vault-dev.hcl    # Vault development config
├── instance/            # Instance-specific files
│   └── certs/          # SSL certificates
├── utils/              # Development utilities
├── vault_utility.py    # Vault integration
├── setup_dev_vault.py  # Development setup script
└── requirements.txt    # Python dependencies
```

## Contributing

Please see CONTRIBUTING.md for guidelines on contributing to this project.

## License

[Your License Here]
