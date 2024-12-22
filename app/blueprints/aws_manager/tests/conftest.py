"""
AWS Manager Test Configuration
---------------------------
Common test fixtures and configuration.
"""

import pytest
from flask import Flask
from app.extensions import db
from .. import aws_manager
from ..models import AWSConfiguration
from unittest.mock import MagicMock

@pytest.fixture
def app():
    """Create and configure a test Flask application"""
    app = Flask(__name__)
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'test-key',
        'WTF_CSRF_ENABLED': False
    })
    
    # Initialize extensions
    db.init_app(app)
    
    # Register blueprint
    app.register_blueprint(aws_manager, url_prefix='/aws')
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    return app

@pytest.fixture
def client(app):
    """Create a test client"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create a test CLI runner"""
    return app.test_cli_runner()

@pytest.fixture
def mock_aws_client():
    """Create a mock AWS client"""
    mock = MagicMock()
    
    # Mock EC2 responses
    mock.describe_instances.return_value = {
        'Reservations': [{
            'Instances': [{
                'InstanceId': 'i-1234567890abcdef0',
                'InstanceType': 't2.micro',
                'State': {'Name': 'running'},
                'PublicIpAddress': '1.2.3.4',
                'PrivateIpAddress': '10.0.0.1',
                'LaunchTime': '2023-01-01T00:00:00Z',
                'Tags': [{'Key': 'Name', 'Value': 'test-instance'}]
            }]
        }]
    }
    
    # Mock Security Group responses
    mock.describe_security_groups.return_value = {
        'SecurityGroups': [{
            'GroupId': 'sg-1234567890abcdef0',
            'GroupName': 'test-group',
            'Description': 'Test security group',
            'VpcId': 'vpc-1234567890abcdef0',
            'IpPermissions': [],
            'IpPermissionsEgress': []
        }]
    }
    
    # Mock IAM responses
    mock.list_users.return_value = {
        'Users': [{
            'UserName': 'test-user',
            'UserId': 'AIDA1234567890ABCDEF0',
            'Arn': 'arn:aws:iam::123456789012:user/test-user',
            'CreateDate': '2023-01-01T00:00:00Z'
        }]
    }
    
    # Mock Health responses
    mock.describe_events.return_value = {
        'events': [{
            'arn': 'arn:aws:health:us-east-1::event/test',
            'service': 'EC2',
            'eventTypeCode': 'AWS_EC2_INSTANCE_ISSUE',
            'eventTypeCategory': 'issue',
            'region': 'us-east-1',
            'startTime': '2023-01-01T00:00:00Z',
            'statusCode': 'open'
        }]
    }
    
    return mock

@pytest.fixture
def mock_vault():
    """Create a mock Vault client"""
    mock = MagicMock()
    mock.get_secret.return_value = {
        'access_key': 'test-access-key',
        'secret_key': 'test-secret-key'
    }
    return mock

@pytest.fixture
def test_config(app):
    """Create a test AWS configuration in the database"""
    with app.app_context():
        config = AWSConfiguration(
            name='test-config',
            regions=['us-east-1', 'us-west-2'],
            vault_path='aws/test-config',
            is_active=True
        )
        db.session.add(config)
        db.session.commit()
        return config

@pytest.fixture
def auth_headers():
    """Create authentication headers for test requests"""
    return {
        'Authorization': 'Bearer test-token',
        'X-Requested-With': 'XMLHttpRequest'
    }

@pytest.fixture
def mock_rbac():
    """Create a mock RBAC decorator"""
    def mock_decorator(*args, **kwargs):
        def wrapper(f):
            return f
        return wrapper
    return mock_decorator

def pytest_configure(config):
    """Configure pytest"""
    # Register custom markers
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as a slow test"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    # Skip slow tests unless explicitly requested
    if not config.getoption("--runslow"):
        skip_slow = pytest.mark.skip(reason="need --runslow option to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)

def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--runslow", action="store_true", default=False, help="run slow tests"
    )
