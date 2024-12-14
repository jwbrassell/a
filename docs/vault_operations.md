# Vault Operations Guide

## Overview

This guide covers the operational aspects of HashiCorp Vault in our environment, including setup, maintenance, and security procedures.

## Installation

### Supported Platforms

- macOS (Intel/ARM) via Homebrew
- Ubuntu via apt repository
- Rocky Linux via yum repository
- Windows 10/11 via direct download

### Development Setup

1. Run the setup script:
```bash
python setup_dev_vault.py
```

2. Update environment variables:
```bash
export VAULT_ADDR=https://127.0.0.1:8200
export VAULT_TOKEN=<token from .env.vault>
```

## Management Scripts

### Unix-like Systems (macOS, Linux)

```bash
# Start Vault
./scripts/vault_manage.sh start

# Stop Vault
./scripts/vault_manage.sh stop

# Check status
./scripts/vault_manage.sh status

# Initialize
./scripts/vault_manage.sh init

# Unseal
./scripts/vault_manage.sh unseal
```

### Windows

```powershell
# Start Vault
.\scripts\vault_manage.ps1 start

# Stop Vault
.\scripts\vault_manage.ps1 stop

# Check status
.\scripts\vault_manage.ps1 status

# Initialize
.\scripts\vault_manage.ps1 init

# Unseal
.\scripts\vault_manage.ps1 unseal
```

## Security Configuration

### SSL/TLS

- Development certificates are generated in instance/certs/
- Production should use proper CA-signed certificates
- Minimum TLS version: 1.2
- Client certificate verification optional

### Access Control

- Localhost-only access in development
- HTTPS required
- Web UI disabled by default
- Token-based authentication

### CSRF Protection

- Automatic token generation and validation
- 24-hour token expiration
- Required for all state-changing operations
- Token storage in Vault

## Plugin Integration

### Credential Management

1. Store plugin credentials:
```python
from vault_utility import VaultUtility

vault = VaultUtility()
vault.plugin_credentials.store_plugin_credentials(
    "plugin-name",
    {
        "api_key": "your-api-key",
        "secret": "your-secret"
    }
)
```

2. Retrieve credentials:
```python
credentials = vault.plugin_credentials.get_plugin_credentials("plugin-name")
```

3. Rotate credentials:
```python
vault.plugin_credentials.rotate_plugin_credentials(
    "plugin-name",
    new_credentials
)
```

## Maintenance Procedures

### Backup and Recovery

1. Backup Vault data:
```bash
# Unix-like systems
tar -czf vault-backup.tar.gz vault-data/

# Windows
Compress-Archive -Path vault-data -DestinationPath vault-backup.zip
```

2. Backup configuration:
```bash
cp config/vault-dev.hcl vault-config-backup.hcl
```

### Monitoring

1. Enable audit logging:
```bash
# Unix-like systems
./scripts/vault_manage.sh audit

# Windows
.\scripts\vault_manage.ps1 audit
```

2. Check logs:
```bash
tail -f logs/vault.log
```

### Health Checks

1. Status check:
```bash
vault status
```

2. Seal status:
```bash
vault operator seal-status
```

## Production Deployment

### Prerequisites

1. SSL/TLS certificates from trusted CA
2. Proper network security groups/firewall rules
3. Sufficient storage for Vault data
4. Monitoring system integration

### Configuration

1. Copy and modify production template:
```bash
cp config/vault-prod.hcl.template /etc/vault.d/vault.hcl
```

2. Update configuration values:
- Storage path
- TLS certificate paths
- API/Cluster addresses
- Telemetry settings
- Audit device paths

### Systemd Service (Linux)

1. Install service file:
```bash
sudo cp config/vault.service /etc/systemd/system/
sudo systemctl daemon-reload
```

2. Enable and start service:
```bash
sudo systemctl enable vault
sudo systemctl start vault
```

## Security Procedures

### Key Rotation

1. Generate new encryption key:
```bash
vault operator generate-root -init
```

2. Rotate encryption key:
```bash
vault operator rotate
```

### Token Management

1. Create new token:
```bash
vault token create -policy=default
```

2. Revoke token:
```bash
vault token revoke <token>
```

### Audit

1. Enable file audit device:
```bash
vault audit enable file file_path=/var/log/vault/audit.log
```

2. Review audit logs:
```bash
tail -f /var/log/vault/audit.log | jq
```

## Troubleshooting

### Common Issues

1. Vault Sealed
```bash
# Check seal status
vault status

# Unseal if needed
vault operator unseal
```

2. TLS Certificate Issues
```bash
# Verify certificate
openssl x509 -in <cert-path> -text -noout

# Check expiration
openssl x509 -in <cert-path> -noout -dates
```

3. Permission Issues
```bash
# Check ownership
ls -l vault-data/

# Fix permissions
chown -R vault:vault vault-data/
chmod 750 vault-data/
```

### Debug Logging

1. Enable debug logging:
```bash
export VAULT_LOG_LEVEL=debug
```

2. Check logs:
```bash
tail -f logs/vault.log
```

## Best Practices

1. Security
- Use strong tokens
- Enable audit logging
- Regular key rotation
- Proper file permissions
- TLS 1.2 minimum

2. Operations
- Regular backups
- Monitor seal status
- Check audit logs
- Update certificates before expiry
- Regular health checks

3. Development
- Use development certificates
- Enable debug logging
- Test plugin integrations
- Validate CSRF protection
- Check token expiration

## Additional Resources

- [HashiCorp Vault Documentation](https://www.vaultproject.io/docs)
- [Security Model](https://www.vaultproject.io/docs/internals/security)
- [Architecture](https://www.vaultproject.io/docs/internals/architecture)
- [API Documentation](https://www.vaultproject.io/api-docs)
