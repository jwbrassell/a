"""
AWS Manager Model Tests
--------------------
Unit tests for AWS Manager models.
"""

import pytest
from datetime import datetime, timezone
from ..models import (
    AWSConfiguration,
    AWSHealthEvent,
    EC2Instance,
    EC2Template
)

@pytest.fixture
def aws_config():
    """Create a test AWS configuration"""
    return AWSConfiguration(
        name='test-config',
        regions=['us-east-1', 'us-west-2'],
        vault_path='aws/test-config',
        is_active=True
    )

@pytest.fixture
def health_event(aws_config):
    """Create a test health event"""
    return AWSHealthEvent(
        aws_config_id=1,
        event_arn='arn:aws:health:us-east-1::event/test',
        service='EC2',
        event_type_code='AWS_EC2_INSTANCE_ISSUE',
        event_type_category='issue',
        region='us-east-1',
        start_time=datetime.now(timezone.utc),
        status='open',
        affected_resources=['i-1234567890abcdef0'],
        description='Test event'
    )

@pytest.fixture
def ec2_instance(aws_config):
    """Create a test EC2 instance"""
    return EC2Instance(
        aws_config_id=1,
        instance_id='i-1234567890abcdef0',
        region='us-east-1',
        instance_type='t2.micro',
        state='running',
        public_ip='1.2.3.4',
        private_ip='10.0.0.1',
        launch_time=datetime.now(timezone.utc),
        tags={'Name': 'test-instance'}
    )

@pytest.fixture
def ec2_template(aws_config):
    """Create a test EC2 template"""
    return EC2Template(
        aws_config_id=1,
        name='test-template',
        description='Test template',
        instance_type='t2.micro',
        ami_id='ami-1234567890abcdef0',
        key_name='test-key',
        security_groups=['sg-1234567890abcdef0'],
        user_data='#!/bin/bash\necho "Hello, World!"',
        tags={'Environment': 'test'}
    )

class TestAWSConfiguration:
    """Test AWS Configuration model"""
    
    def test_create_config(self, aws_config):
        """Test creating a configuration"""
        assert aws_config.name == 'test-config'
        assert 'us-east-1' in aws_config.regions
        assert aws_config.vault_path == 'aws/test-config'
        assert aws_config.is_active is True
        
    def test_config_timestamps(self, aws_config):
        """Test configuration timestamps"""
        assert isinstance(aws_config.created_at, datetime)
        assert isinstance(aws_config.updated_at, datetime)

class TestAWSHealthEvent:
    """Test AWS Health Event model"""
    
    def test_create_event(self, health_event):
        """Test creating a health event"""
        assert health_event.service == 'EC2'
        assert health_event.event_type_code == 'AWS_EC2_INSTANCE_ISSUE'
        assert health_event.status == 'open'
        assert len(health_event.affected_resources) == 1
        
    def test_event_timestamps(self, health_event):
        """Test event timestamps"""
        assert isinstance(health_event.start_time, datetime)
        assert health_event.end_time is None

class TestEC2Instance:
    """Test EC2 Instance model"""
    
    def test_create_instance(self, ec2_instance):
        """Test creating an EC2 instance"""
        assert ec2_instance.instance_id == 'i-1234567890abcdef0'
        assert ec2_instance.instance_type == 't2.micro'
        assert ec2_instance.state == 'running'
        assert ec2_instance.public_ip == '1.2.3.4'
        
    def test_instance_to_dict(self, ec2_instance):
        """Test instance to dictionary conversion"""
        data = ec2_instance.to_dict()
        assert data['instance_id'] == ec2_instance.instance_id
        assert data['instance_type'] == ec2_instance.instance_type
        assert data['state'] == ec2_instance.state
        assert data['tags'] == ec2_instance.tags

class TestEC2Template:
    """Test EC2 Template model"""
    
    def test_create_template(self, ec2_template):
        """Test creating an EC2 template"""
        assert ec2_template.name == 'test-template'
        assert ec2_template.instance_type == 't2.micro'
        assert ec2_template.ami_id == 'ami-1234567890abcdef0'
        assert len(ec2_template.security_groups) == 1
        
    def test_template_to_dict(self, ec2_template):
        """Test template to dictionary conversion"""
        data = ec2_template.to_dict()
        assert data['name'] == ec2_template.name
        assert data['instance_type'] == ec2_template.instance_type
        assert data['ami_id'] == ec2_template.ami_id
        assert data['tags'] == ec2_template.tags
        
    def test_get_launch_config(self, ec2_template):
        """Test getting launch configuration"""
        config = ec2_template.get_launch_config()
        assert config['instance_type'] == ec2_template.instance_type
        assert config['ami_id'] == ec2_template.ami_id
        assert config['key_name'] == ec2_template.key_name
        assert config['security_groups'] == ec2_template.security_groups
