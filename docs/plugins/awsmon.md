# AWS Monitor Plugin

## Overview

The AWS Monitor plugin provides comprehensive AWS infrastructure monitoring and management capabilities including:
- EC2 instance monitoring across multiple regions
- Synthetic testing and monitoring
- Jump server management
- Secure credential management via HashiCorp Vault

## Features

### EC2 Instance Monitoring
- Real-time instance status monitoring
- Multi-region support
- Instance management (start/stop/terminate)
- Instance metadata and tag tracking
- Automatic state change logging

### Synthetic Testing
- Multiple test types:
  - Ping tests
  - Traceroute analysis
  - Port availability checks
  - HTTP endpoint monitoring
- Configurable test frequencies
- Detailed test results and history
- Response time tracking
- Custom test parameters

### Jump Server Management
- Template-based deployment
- Security group configuration
- User data scripts
- Automated provisioning

## Installation

1. Ensure Vault is installed and configured:
```bash
# Install Vault
brew install vault  # macOS
# or
sudo apt-get install vault  # Ubuntu

# Start Vault in dev mode (for testing)
vault server -dev
```

2. Configure AWS credentials in Vault:
```bash
# Enable AWS secrets engine
vault secrets enable aws

# Configure AWS credentials
vault write aws/config/root \
    access_key=<AWS_ACCESS_KEY> \
    secret_key=<AWS_SECRET_KEY> \
    region=us-east-1
```

3. Set required environment variables:
```bash
export VAULT_ADDR='http://127.0.0.1:8200'
export VAULT_TOKEN='your-token'
```

## Configuration

### AWS Credentials

1. Navigate to Settings > AWS Settings
2. Click "Add Credentials"
3. Enter AWS access key and secret key
4. Select enabled regions
5. Save credentials (they will be stored in Vault)

### Regions

1. Navigate to Settings > AWS Settings
2. Click "Add Region"
3. Enter region name and code (e.g., "US East 1", "us-east-1")
4. Save region

### Jump Server Templates

1. Navigate to Settings > AWS Settings
2. Click "New Template"
3. Configure:
   - Template name
   - AMI ID
   - Instance type
   - Security groups
   - User data script
4. Save template

## API Endpoints

### Instance Management
```
GET /api/instances
POST /api/instances/<instance_id>/action
```

### Synthetic Testing
```
GET /api/synthetic/tests
POST /api/synthetic/tests
GET /api/synthetic/results
```

### Templates
```
GET /api/templates
POST /api/templates
```

## Permissions

The plugin requires the following permissions:
- awsmon_dashboard_access
- awsmon_instances_access
- awsmon_synthetic_access
- awsmon_templates_access
- awsmon_settings_access

## Models

### AWSRegion
- Tracks AWS regions for monitoring
- Fields: name, code, created_by, updated_by, deleted_at

### EC2Instance
- Represents EC2 instances
- Fields: instance_id, name, region_id, instance_type, state, etc.
- Tracks: created_by, updated_by, deleted_at

### JumpServerTemplate
- Templates for jump server deployment
- Fields: name, ami_id, instance_type, security_groups, user_data
- Tracks: created_by, updated_by, deleted_at

### SyntheticTest
- Defines synthetic monitoring tests
- Fields: name, test_type, target, frequency, timeout, etc.
- Tracks: created_by, updated_by, deleted_at

### TestResult
- Stores synthetic test results
- Fields: test_id, instance_id, status, response_time, etc.
- Tracks: created_by

### AWSCredential
- Manages AWS credential references in Vault
- Fields: name, vault_path, regions
- Tracks: created_by, updated_by, deleted_at

### ChangeLog
- Tracks changes to AWS resources
- Fields: action, resource_type, resource_id, details
- Tracks: created_by

## Best Practices

1. **Credential Management**
   - Rotate credentials regularly
   - Use minimal required permissions
   - Monitor credential usage

2. **Synthetic Testing**
   - Start with basic tests
   - Gradually increase complexity
   - Set appropriate timeouts
   - Monitor test frequency impact

3. **Jump Servers**
   - Use hardened AMIs
   - Implement proper security groups
   - Regular security updates
   - Monitor access logs

4. **Monitoring**
   - Set up alerts for critical changes
   - Regular backup of test results
   - Monitor resource usage
   - Track cost implications

## Troubleshooting

### Common Issues

1. **Vault Connection**
   - Verify Vault is running
   - Check environment variables
   - Validate token permissions

2. **AWS API**
   - Verify credentials
   - Check IAM permissions
   - Validate region settings

3. **Synthetic Tests**
   - Check network connectivity
   - Verify instance permissions
   - Review timeout settings

4. **Database**
   - Check migrations
   - Verify table permissions
   - Monitor storage usage
