"""
AWS Manager Tests
--------------
Tests for AWS Manager utility class.
"""

import pytest
from datetime import datetime, timezone
from ..utils.aws import AWSManager, get_aws_manager
from ..models import AWSConfiguration
from unittest.mock import patch, MagicMock

@pytest.fixture
def aws_manager():
    """Create an AWS manager instance"""
    return AWSManager(
        access_key='test-access-key',
        secret_key='test-secret-key',
        regions=['us-east-1', 'us-west-2'],
        verify_ssl=True
    )

class TestAWSManager:
    """Test AWS Manager utility"""
    
    def test_initialization(self, aws_manager):
        """Test AWS manager initialization"""
        assert aws_manager.access_key == 'test-access-key'
        assert aws_manager.secret_key == 'test-secret-key'
        assert 'us-east-1' in aws_manager.regions
        assert aws_manager.verify_ssl is True
        
    def test_get_client(self, aws_manager, mock_aws_client):
        """Test getting AWS client"""
        with patch('boto3.client', return_value=mock_aws_client):
            client = aws_manager._get_client('ec2', 'us-east-1')
            assert client == mock_aws_client
            
            # Test client caching
            cached_client = aws_manager._get_client('ec2', 'us-east-1')
            assert cached_client == client

    def test_get_security_groups(self, aws_manager, mock_aws_client):
        """Test getting security groups"""
        with patch('boto3.client', return_value=mock_aws_client):
            groups = aws_manager.get_security_groups('us-east-1')
            assert len(groups) == 1
            group = groups[0]
            assert group['group_id'] == 'sg-1234567890abcdef0'
            assert group['group_name'] == 'test-group'
            assert group['region'] == 'us-east-1'

    def test_create_security_group(self, aws_manager, mock_aws_client):
        """Test creating security group"""
        mock_aws_client.create_security_group.return_value = {
            'GroupId': 'sg-1234567890abcdef0'
        }
        
        with patch('boto3.client', return_value=mock_aws_client):
            group = aws_manager.create_security_group(
                region='us-east-1',
                name='test-group',
                description='Test security group',
                vpc_id='vpc-1234567890abcdef0'
            )
            assert group['group_id'] == 'sg-1234567890abcdef0'
            assert group['group_name'] == 'test-group'
            assert group['vpc_id'] == 'vpc-1234567890abcdef0'

    def test_get_iam_users(self, aws_manager, mock_aws_client):
        """Test getting IAM users"""
        with patch('boto3.client', return_value=mock_aws_client):
            users = aws_manager.get_iam_users()
            assert len(users) == 1
            user = users[0]
            assert user['username'] == 'test-user'
            assert user['user_id'] == 'AIDA1234567890ABCDEF0'

    def test_create_iam_user(self, aws_manager, mock_aws_client):
        """Test creating IAM user"""
        mock_aws_client.create_user.return_value = {
            'User': {
                'UserName': 'test-user',
                'UserId': 'AIDA1234567890ABCDEF0',
                'Arn': 'arn:aws:iam::123456789012:user/test-user',
                'CreateDate': datetime.now(timezone.utc)
            }
        }
        mock_aws_client.create_access_key.return_value = {
            'AccessKey': {
                'AccessKeyId': 'AKIA1234567890ABCDEF0',
                'SecretAccessKey': 'test-secret-key'
            }
        }
        
        with patch('boto3.client', return_value=mock_aws_client):
            result = aws_manager.create_iam_user('test-user')
            assert result['username'] == 'test-user'
            assert 'access_key' in result
            assert result['access_key']['AccessKeyId'] == 'AKIA1234567890ABCDEF0'

    def test_get_health_events(self, aws_manager, mock_aws_client):
        """Test getting health events"""
        mock_aws_client.describe_event_details.return_value = {
            'successfulSet': [{
                'eventDescription': {
                    'latestDescription': 'Test event description'
                }
            }]
        }
        mock_aws_client.describe_affected_entities.return_value = {
            'entities': [{
                'entityValue': 'i-1234567890abcdef0'
            }]
        }
        
        with patch('boto3.client', return_value=mock_aws_client):
            events = aws_manager.get_health_events(1)
            assert len(events) == 1
            event = events[0]
            assert event['service'] == 'EC2'
            assert event['event_type_code'] == 'AWS_EC2_INSTANCE_ISSUE'
            assert event['status'] == 'open'
            assert len(event['affected_resources']) == 1

class TestGetAWSManager:
    """Test get_aws_manager helper function"""
    
    def test_get_aws_manager_success(self, app, test_config, mock_vault):
        """Test successful AWS manager creation"""
        with app.app_context():
            with patch('vault_utility.VaultUtility', return_value=mock_vault):
                manager = get_aws_manager(test_config.id)
                assert isinstance(manager, AWSManager)
                assert manager.access_key == 'test-access-key'
                assert manager.secret_key == 'test-secret-key'
                assert test_config.regions == manager.regions

    def test_get_aws_manager_invalid_config(self, app):
        """Test AWS manager creation with invalid config"""
        with app.app_context():
            with pytest.raises(Exception):
                get_aws_manager(999)  # Non-existent config ID

    def test_get_aws_manager_no_credentials(self, app, test_config, mock_vault):
        """Test AWS manager creation with missing credentials"""
        mock_vault.get_secret.return_value = None
        with app.app_context():
            with patch('vault_utility.VaultUtility', return_value=mock_vault):
                with pytest.raises(Exception):
                    get_aws_manager(test_config.id)

@pytest.mark.integration
class TestAWSManagerIntegration:
    """Integration tests for AWS Manager"""
    
    def test_full_security_group_lifecycle(self, aws_manager, mock_aws_client):
        """Test complete security group lifecycle"""
        with patch('boto3.client', return_value=mock_aws_client):
            # Create security group
            group = aws_manager.create_security_group(
                region='us-east-1',
                name='test-group',
                description='Test security group',
                vpc_id='vpc-1234567890abcdef0'
            )
            group_id = group['group_id']
            
            # Add rules
            aws_manager.add_security_group_rules(
                region='us-east-1',
                group_id=group_id,
                rules=[{
                    'IpProtocol': 'tcp',
                    'FromPort': 80,
                    'ToPort': 80,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                }]
            )
            
            # Get and verify group
            groups = aws_manager.get_security_groups('us-east-1')
            group = next(g for g in groups if g['group_id'] == group_id)
            assert group['group_name'] == 'test-group'
            
            # Delete group
            assert aws_manager.delete_security_group('us-east-1', group_id)

    def test_full_iam_user_lifecycle(self, aws_manager, mock_aws_client):
        """Test complete IAM user lifecycle"""
        with patch('boto3.client', return_value=mock_aws_client):
            # Create user
            result = aws_manager.create_iam_user('test-user')
            username = result['username']
            
            # Get user details
            details = aws_manager.get_iam_user_details(username)
            assert 'access_keys' in details
            
            # Rotate access key
            new_key = aws_manager.rotate_access_key(username)
            assert 'AccessKeyId' in new_key
            
            # Delete user
            assert aws_manager.delete_iam_user(username)
