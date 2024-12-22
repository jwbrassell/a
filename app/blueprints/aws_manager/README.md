# AWS Manager Blueprint

A comprehensive Flask blueprint for managing AWS resources with real-time monitoring capabilities.

## Features

### AWS Health Events
- Real-time health event monitoring via WebSocket
- Event filtering and categorization
- Browser notifications for critical events
- Event history tracking
- Configurable refresh intervals

### EC2 Management
- Instance lifecycle management
- Instance status monitoring
- Template-based instance creation
- Multi-region support
- Bulk operations support

### Security Groups
- Security group CRUD operations
- Rule management (inbound/outbound)
- CIDR validation
- Protocol and port range configuration
- VPC integration

### IAM User Management
- User lifecycle management
- Access key rotation
- Policy management
- Group management
- Permission controls

## Installation

1. Register the blueprint in your Flask application:

```python
from flask import Flask
from app.blueprints.aws_manager import aws_manager

app = Flask(__name__)
app.register_blueprint(aws_manager, url_prefix='/aws')
```

2. Configure AWS credentials in Vault:

```bash
# Store AWS credentials
vault kv put aws/my-config \
    access_key=YOUR_ACCESS_KEY \
    secret_key=YOUR_SECRET_KEY
```

3. Set up the database:

```python
from app.extensions import db
from app.blueprints.aws_manager.models import *

db.create_all()
```

## Configuration

### Required Environment Variables

- `VAULT_ADDR`: Vault server address
- `VAULT_TOKEN`: Vault authentication token
- `AWS_DEFAULT_REGION`: Default AWS region

### Optional Settings

- `AWS_VERIFY_SSL`: Enable/disable SSL verification (default: True)
- `AWS_MAX_RETRIES`: Maximum API retry attempts (default: 3)
- `HEALTH_EVENT_HISTORY`: Maximum events to keep in history (default: 10)

## Usage

### Managing AWS Configurations

```python
from app.blueprints.aws_manager.models import AWSConfiguration

# Create configuration
config = AWSConfiguration(
    name='production',
    regions=['us-east-1', 'us-west-2'],
    vault_path='aws/production'
)
db.session.add(config)
db.session.commit()
```

### Working with EC2 Instances

```python
from app.blueprints.aws_manager.utils import get_aws_manager

# Get AWS manager instance
aws = get_aws_manager(config_id)

# Launch instance from template
template = EC2Template.query.get(template_id)
aws.launch_ec2_instance(region, template.get_launch_config())
```

### Managing Security Groups

```python
# Create security group
group = aws.create_security_group(
    region='us-east-1',
    name='web-servers',
    description='Web server security group',
    vpc_id='vpc-1234567890abcdef0'
)

# Add inbound rule
aws.add_security_group_rules(
    region='us-east-1',
    group_id=group['group_id'],
    rules=[{
        'IpProtocol': 'tcp',
        'FromPort': 80,
        'ToPort': 80,
        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
    }],
    rule_type='ingress'
)
```

### Managing IAM Users

```python
# Create user with access key
result = aws.create_iam_user('john.doe', create_access_key=True)

# Attach policy
aws.attach_user_policy(
    'john.doe',
    'arn:aws:iam::aws:policy/AmazonEC2ReadOnlyAccess'
)

# Add to group
aws.add_user_to_group('john.doe', 'Developers')
```

## WebSocket Integration

The AWS Manager provides real-time health event notifications via WebSocket:

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://your-server/aws/health-events');

// Handle events
ws.onmessage = (event) => {
    const healthEvent = JSON.parse(event.data);
    console.log('New health event:', healthEvent);
};
```

## Testing

The blueprint includes comprehensive tests:

```bash
# Run all tests
pytest app/blueprints/aws_manager/tests/

# Run specific test categories
pytest app/blueprints/aws_manager/tests/test_models.py
pytest app/blueprints/aws_manager/tests/test_routes.py
pytest app/blueprints/aws_manager/tests/test_aws_manager.py
pytest app/blueprints/aws_manager/tests/test_websocket.py

# Run integration tests
pytest -m integration

# Run with coverage
pytest --cov=app.blueprints.aws_manager
```

## Project Structure

```
aws_manager/
├── __init__.py
├── constants.py
├── models/
│   ├── __init__.py
│   ├── aws_configuration.py
│   ├── health_event.py
│   ├── ec2_instance.py
│   └── ec2_template.py
├── routes/
│   ├── __init__.py
│   ├── configurations.py
│   ├── health_events.py
│   ├── ec2.py
│   ├── templates.py
│   ├── security_groups.py
│   └── iam.py
├── utils/
│   ├── __init__.py
│   ├── aws.py
│   └── websocket_service.py
├── static/
│   └── js/
│       ├── health_events.js
│       ├── security_groups.js
│       └── iam_users.js
├── templates/
│   └── aws/
│       ├── base_aws.html
│       ├── configurations.html
│       ├── ec2_instances.html
│       ├── templates.html
│       ├── security_groups.html
│       └── iam_users.html
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_models.py
    ├── test_routes.py
    ├── test_aws_manager.py
    └── test_websocket.py
```

## Contributing

1. Follow the established package structure
2. Maintain modular design principles
3. Add proper documentation
4. Include error handling
5. Add appropriate tests
6. Update the implementation tracking document

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Security

- All AWS credentials are stored in Vault
- RBAC controls access to resources
- SSL verification enabled by default
- Access key rotation support
- Comprehensive audit logging

## Support

For issues and feature requests, please use the GitHub issue tracker.
