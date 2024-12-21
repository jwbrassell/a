# AWS Manager API Documentation

## Base URL

All endpoints are prefixed with `/aws`.

## Authentication

All endpoints require authentication. Use the following headers:
- `Authorization`: Bearer token for authentication
- `X-Requested-With`: 'XMLHttpRequest' for AJAX requests

## Response Format

All responses are in JSON format with the following structure:

```json
{
    "data": {},      // Response data
    "message": "",   // Optional success/error message
    "error": ""      // Optional error details
}
```

## Endpoints

### AWS Configurations

#### List Configurations
```
GET /configurations
```
Returns list of AWS configurations.

Response:
```json
{
    "data": [{
        "id": 1,
        "name": "production",
        "regions": ["us-east-1"],
        "created_at": "2023-01-01T00:00:00Z"
    }]
}
```

#### Create Configuration
```
POST /configurations
```
Create new AWS configuration.

Request:
```json
{
    "name": "production",
    "regions": ["us-east-1"],
    "access_key": "YOUR_ACCESS_KEY",
    "secret_key": "YOUR_SECRET_KEY"
}
```

Response:
```json
{
    "data": {
        "id": 1,
        "name": "production",
        "regions": ["us-east-1"],
        "created_at": "2023-01-01T00:00:00Z"
    },
    "message": "Configuration created successfully"
}
```

#### Delete Configuration
```
DELETE /configurations/{config_id}
```
Delete AWS configuration.

### Health Events

#### List Health Events
```
GET /configurations/{config_id}/health
```
Returns list of AWS health events.

Query Parameters:
- `region` (optional): Filter by region

Response:
```json
{
    "data": [{
        "event_arn": "arn:aws:health:region:event/id",
        "service": "EC2",
        "event_type_code": "AWS_EC2_INSTANCE_ISSUE",
        "status": "open",
        "affected_resources": ["i-1234567890abcdef0"]
    }]
}
```

#### Refresh Health Events
```
POST /configurations/{config_id}/health/refresh
```
Force refresh of health events.

### EC2 Instances

#### List EC2 Instances
```
GET /configurations/{config_id}/ec2
```
Returns list of EC2 instances.

Query Parameters:
- `region` (optional): Filter by region
- `next_token` (optional): Pagination token

Response:
```json
{
    "data": {
        "instances": [{
            "instance_id": "i-1234567890abcdef0",
            "instance_type": "t2.micro",
            "state": "running",
            "public_ip": "1.2.3.4"
        }],
        "next_token": "token"
    }
}
```

#### Launch EC2 Instance
```
POST /configurations/{config_id}/ec2
```
Launch new EC2 instance(s).

Request:
```json
{
    "region": "us-east-1",
    "template_id": 1,
    "count": 1
}
```

#### Control EC2 Instance
```
POST /configurations/{config_id}/ec2/{instance_id}/{action}
```
Control EC2 instance state.

Parameters:
- `action`: One of 'start', 'stop', 'terminate'

Headers:
- `X-AWS-Region`: AWS region

### Security Groups

#### List Security Groups
```
GET /configurations/{config_id}/security-groups
```
Returns list of security groups.

Query Parameters:
- `region` (optional): Filter by region

Response:
```json
{
    "data": [{
        "group_id": "sg-1234567890abcdef0",
        "group_name": "web-servers",
        "description": "Web server security group",
        "vpc_id": "vpc-1234567890abcdef0",
        "inbound_rules": [],
        "outbound_rules": []
    }]
}
```

#### Create Security Group
```
POST /configurations/{config_id}/security-groups
```
Create new security group.

Request:
```json
{
    "name": "web-servers",
    "description": "Web server security group",
    "vpc_id": "vpc-1234567890abcdef0",
    "region": "us-east-1"
}
```

#### Add Security Group Rules
```
POST /configurations/{config_id}/security-groups/{group_id}/rules
```
Add rules to security group.

Request:
```json
{
    "rules": [{
        "IpProtocol": "tcp",
        "FromPort": 80,
        "ToPort": 80,
        "IpRanges": [{
            "CidrIp": "0.0.0.0/0"
        }]
    }],
    "rule_type": "ingress",
    "region": "us-east-1"
}
```

### IAM Users

#### List IAM Users
```
GET /configurations/{config_id}/iam
```
Returns list of IAM users.

Response:
```json
{
    "data": [{
        "username": "john.doe",
        "user_id": "AIDA1234567890ABCDEF0",
        "arn": "arn:aws:iam::account:user/john.doe",
        "created_date": "2023-01-01T00:00:00Z"
    }]
}
```

#### Create IAM User
```
POST /configurations/{config_id}/iam
```
Create new IAM user.

Request:
```json
{
    "username": "john.doe",
    "create_access_key": true,
    "policies": [
        "arn:aws:iam::aws:policy/AmazonEC2ReadOnlyAccess"
    ],
    "groups": ["Developers"]
}
```

#### Rotate Access Key
```
POST /configurations/{config_id}/iam/{username}/rotate-key
```
Rotate user's access key.

Response:
```json
{
    "data": {
        "AccessKeyId": "AKIA1234567890ABCDEF0",
        "SecretAccessKey": "secret",
        "CreateDate": "2023-01-01T00:00:00Z"
    }
}
```

## WebSocket API

### Health Event WebSocket
```
ws://your-server/aws/health-events
```

Message Format:
```json
{
    "event_arn": "arn:aws:health:region:event/id",
    "service": "EC2",
    "event_type_code": "AWS_EC2_INSTANCE_ISSUE",
    "status": "open",
    "affected_resources": ["i-1234567890abcdef0"],
    "description": "Event description"
}
```

## Error Codes

- 400: Bad Request - Invalid parameters
- 401: Unauthorized - Missing or invalid authentication
- 403: Forbidden - Insufficient permissions
- 404: Not Found - Resource not found
- 409: Conflict - Resource already exists
- 500: Internal Server Error - Server-side error

## Rate Limiting

- Default: 100 requests per minute per IP
- WebSocket: 10 connections per IP
- Bulk operations: 5 requests per minute

## Pagination

Endpoints that return lists support pagination using:
- `next_token`: Token for next page
- `limit`: Items per page (default: 20, max: 100)

## CORS

CORS is enabled for all endpoints with the following settings:
- Allowed origins: Configurable
- Allowed methods: GET, POST, PUT, DELETE
- Allowed headers: Content-Type, Authorization, X-Requested-With
- Max age: 3600

## Versioning

The API version is included in the response headers:
```
X-API-Version: 1.0.0
```

## Examples

### JavaScript

```javascript
// List EC2 instances
async function listInstances(configId) {
    const response = await fetch(`/aws/configurations/${configId}/ec2`, {
        headers: {
            'Authorization': 'Bearer token',
            'X-Requested-With': 'XMLHttpRequest'
        }
    });
    return response.json();
}

// Create security group
async function createSecurityGroup(configId, data) {
    const response = await fetch(`/aws/configurations/${configId}/security-groups`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer token',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(data)
    });
    return response.json();
}

// Connect to WebSocket
const ws = new WebSocket('ws://your-server/aws/health-events');
ws.onmessage = (event) => {
    const healthEvent = JSON.parse(event.data);
    console.log('New health event:', healthEvent);
};
```

### Python

```python
import requests

class AWSManagerClient:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {token}',
            'X-Requested-With': 'XMLHttpRequest'
        }
    
    def list_instances(self, config_id, region=None):
        params = {'region': region} if region else {}
        response = requests.get(
            f'{self.base_url}/configurations/{config_id}/ec2',
            headers=self.headers,
            params=params
        )
        return response.json()
    
    def create_security_group(self, config_id, data):
        response = requests.post(
            f'{self.base_url}/configurations/{config_id}/security-groups',
            headers=self.headers,
            json=data
        )
        return response.json()
