# Plugin Vault Integration Guide

## Overview

This guide explains how to integrate HashiCorp Vault with your plugins for secure credential management. Our Vault integration provides a secure way to store and manage plugin credentials, API keys, and other secrets.

## Quick Start

### 1. Basic Usage

```python
from vault_utility import VaultUtility

def initialize_plugin():
    vault = VaultUtility()
    credentials = vault.plugin_credentials.get_plugin_credentials("your-plugin-name")
    return credentials

# Example usage in your plugin
credentials = initialize_plugin()
api_key = credentials.get('api_key')
secret = credentials.get('secret')
```

### 2. Using the CLI Tool

```bash
# Store credentials
python utils/manage_plugin_credentials.py store your-plugin-name credentials.json

# Retrieve credentials
python utils/manage_plugin_credentials.py get your-plugin-name

# Rotate credentials
python utils/manage_plugin_credentials.py rotate your-plugin-name new-credentials.json
```

## Credential Management

### Storing Credentials

```python
from vault_utility import VaultUtility

vault = VaultUtility()

# Store initial credentials
credentials = {
    'api_key': 'your-api-key',
    'secret': 'your-secret',
    'additional_config': {
        'endpoint': 'https://api.example.com',
        'timeout': 30
    }
}

vault.plugin_credentials.store_plugin_credentials('your-plugin-name', credentials)
```

### Retrieving Credentials

```python
# Get current credentials
credentials = vault.plugin_credentials.get_plugin_credentials('your-plugin-name')

# Handle missing credentials
if credentials is None:
    raise ValueError("Plugin credentials not found")

# Access specific values
api_key = credentials.get('api_key')
secret = credentials.get('secret')
config = credentials.get('additional_config', {})
```

### Rotating Credentials

```python
# Rotate to new credentials
new_credentials = {
    'api_key': 'new-api-key',
    'secret': 'new-secret',
    'additional_config': {
        'endpoint': 'https://api.example.com',
        'timeout': 30
    }
}

vault.plugin_credentials.rotate_plugin_credentials('your-plugin-name', new_credentials)
```

## Best Practices

### 1. Error Handling

Always implement proper error handling for Vault operations:

```python
from vault_utility import VaultUtility, VaultError

def get_plugin_credentials():
    try:
        vault = VaultUtility()
        credentials = vault.plugin_credentials.get_plugin_credentials('your-plugin-name')
        if not credentials:
            raise ValueError("Plugin credentials not found")
        return credentials
    except VaultError as e:
        logger.error(f"Vault error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
```

### 2. Credential Validation

Validate credentials before using them:

```python
def validate_credentials(credentials):
    required_fields = ['api_key', 'secret']
    
    # Check required fields
    for field in required_fields:
        if field not in credentials:
            raise ValueError(f"Missing required field: {field}")
            
    # Validate format
    if not isinstance(credentials['api_key'], str):
        raise ValueError("API key must be a string")
        
    # Validate content
    if len(credentials['api_key']) < 10:
        raise ValueError("API key too short")
```

### 3. Secure Configuration

Store sensitive configuration in Vault:

```python
# Good: Store in Vault
credentials = {
    'api_key': 'secret-key',
    'webhook_url': 'https://api.example.com/webhook',
    'oauth': {
        'client_id': 'client-id',
        'client_secret': 'client-secret'
    }
}

# Bad: Hard-coded credentials
API_KEY = 'secret-key'  # Don't do this
```

### 4. Credential Rotation

Implement credential rotation in your plugin:

```python
class PluginAPI:
    def __init__(self):
        self.vault = VaultUtility()
        self.credentials = None
        
    def refresh_credentials(self):
        """Refresh credentials from Vault."""
        self.credentials = self.vault.plugin_credentials.get_plugin_credentials('your-plugin-name')
        
    def rotate_credentials(self, new_credentials):
        """Rotate to new credentials."""
        try:
            # Verify new credentials work
            self.test_credentials(new_credentials)
            
            # Store new credentials
            self.vault.plugin_credentials.rotate_plugin_credentials(
                'your-plugin-name',
                new_credentials
            )
            
            # Update local reference
            self.credentials = new_credentials
            
        except Exception as e:
            logger.error(f"Credential rotation failed: {e}")
            raise
            
    def test_credentials(self, credentials):
        """Test if credentials are valid."""
        # Implement credential testing logic
        pass
```

## CSRF Protection

### 1. Protecting Routes

Use the CSRF protection decorator:

```python
from vault_utility import csrf_protected
from flask import Blueprint

bp = Blueprint('your_plugin', __name__)

@bp.route('/api/data', methods=['POST'])
@csrf_protected
def update_data():
    # Your route logic here
    pass
```

### 2. Including CSRF Token

Include the CSRF token in requests:

```javascript
// Frontend JavaScript
async function makeRequest() {
    const response = await fetch('/api/data', {
        method: 'POST',
        headers: {
            'X-CSRF-Token': csrfToken,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    });
}
```

## Development Tools

### 1. Credential Management CLI

```bash
# List all plugins with stored credentials
python utils/manage_plugin_credentials.py list

# Validate credentials
python utils/manage_plugin_credentials.py validate your-plugin-name

# Delete credentials
python utils/manage_plugin_credentials.py delete your-plugin-name
```

### 2. Verification Script

```bash
# Verify Vault setup
python utils/verify_vault_setup.py
```

## Testing

### 1. Mock Vault in Tests

```python
from unittest.mock import patch

def test_plugin_initialization():
    mock_credentials = {
        'api_key': 'test-key',
        'secret': 'test-secret'
    }
    
    with patch('vault_utility.VaultUtility') as mock_vault:
        mock_vault.return_value.plugin_credentials.get_plugin_credentials.return_value = mock_credentials
        
        # Test your plugin initialization
        plugin = YourPlugin()
        assert plugin.api_key == 'test-key'
```

### 2. Integration Tests

```python
def test_credential_rotation():
    vault = VaultUtility()
    
    # Store test credentials
    initial_creds = {'api_key': 'initial-key'}
    vault.plugin_credentials.store_plugin_credentials('test-plugin', initial_creds)
    
    # Rotate credentials
    new_creds = {'api_key': 'new-key'}
    vault.plugin_credentials.rotate_plugin_credentials('test-plugin', new_creds)
    
    # Verify rotation
    current_creds = vault.plugin_credentials.get_plugin_credentials('test-plugin')
    assert current_creds['api_key'] == 'new-key'
```

## Troubleshooting

### Common Issues

1. Credentials Not Found
```python
# Check if plugin path is correct
vault.list_secrets('plugins')

# Verify credentials exist
credentials = vault.plugin_credentials.get_plugin_credentials('your-plugin-name')
```

2. CSRF Token Invalid
```python
# Generate new token
token = vault.csrf.generate_token()

# Validate token
is_valid = vault.csrf.validate_token(token)
```

3. Vault Connection Issues
```python
# Verify Vault is running
python utils/verify_vault_setup.py

# Check environment variables
echo $VAULT_ADDR
echo $VAULT_TOKEN
```

## Security Considerations

1. Never log credentials
2. Rotate credentials regularly
3. Use CSRF protection for all state-changing operations
4. Validate all credentials before use
5. Implement proper error handling
6. Use secure communication (HTTPS)
7. Follow the principle of least privilege

## Additional Resources

- [Vault Documentation](https://www.vaultproject.io/docs)
- [Plugin Development Guide](docs/plugin_template.md)
- [Security Best Practices](docs/security.md)
