# AWS Monitoring Plugin

A comprehensive AWS monitoring and management plugin for Flask Black Friday Lunch that provides:
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

### Security
- HashiCorp Vault integration for AWS credentials
- Secure credential rotation
- Access logging
- Role-based access control

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

4. Run database migrations:
```bash
flask db upgrade
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

## Synthetic Testing

### Creating Tests

1. Navigate to Synthetic Tests
2. Click "New Test"
3. Configure:
   - Test name
   - Test type (ping, traceroute, port check, HTTP)
   - Target (IP, hostname, or URL)
   - Source instance
   - Frequency
   - Timeout
   - Additional parameters based on test type

### Test Types

#### Ping Test
- Basic connectivity testing
- Measures response time
- Packet loss monitoring

#### Traceroute Test
- Network path analysis
- Hop-by-hop latency
- Route visualization

#### Port Check
- TCP port availability
- Connection time measurement
- Custom port specification

#### HTTP Check
- Endpoint availability
- Status code verification
- Response time tracking
- Custom HTTP methods

## Dashboard

The main dashboard provides:
- Instance status overview
- Region-wise instance distribution
- Synthetic test results
- Recent changes log
- Quick action buttons

### Metrics

- Instance count by state
- Instance count by region
- Test success/failure rates
- Response time trends
- Alert counts

### Actions

- Start/Stop instances
- Launch new instances
- Clone instances
- Configure monitoring
- Manage tests

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

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Create pull request

## License

This plugin is part of Flask Black Friday Lunch and follows its licensing terms.
