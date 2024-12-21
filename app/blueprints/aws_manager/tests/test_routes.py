"""
AWS Manager Route Tests
--------------------
Tests for AWS Manager route handlers.
"""

import pytest
import json
from datetime import datetime, timezone
from unittest.mock import patch

class TestConfigurationRoutes:
    """Test configuration management routes"""
    
    def test_list_configurations(self, client, test_config, auth_headers):
        """Test listing configurations"""
        response = client.get('/aws/configurations', headers=auth_headers)
        assert response.status_code == 200
        assert b'test-config' in response.data
        
    def test_create_configuration(self, client, mock_vault, auth_headers):
        """Test creating configuration"""
        with patch('vault_utility.VaultUtility', return_value=mock_vault):
            data = {
                'name': 'new-config',
                'regions': ['us-east-1'],
                'access_key': 'test-key',
                'secret_key': 'test-secret'
            }
            response = client.post('/aws/configurations',
                                 json=data,
                                 headers=auth_headers)
            assert response.status_code == 201
            result = json.loads(response.data)
            assert result['name'] == 'new-config'
            
    def test_delete_configuration(self, client, test_config, mock_vault, auth_headers):
        """Test deleting configuration"""
        with patch('vault_utility.VaultUtility', return_value=mock_vault):
            response = client.delete(f'/aws/configurations/{test_config.id}',
                                   headers=auth_headers)
            assert response.status_code == 204

class TestHealthEventRoutes:
    """Test health event routes"""
    
    def test_list_health_events(self, client, test_config, mock_aws_client, auth_headers):
        """Test listing health events"""
        with patch('boto3.client', return_value=mock_aws_client):
            response = client.get(f'/aws/configurations/{test_config.id}/health',
                                headers=auth_headers)
            assert response.status_code == 200
            assert b'AWS_EC2_INSTANCE_ISSUE' in response.data
            
    def test_refresh_health_events(self, client, test_config, mock_aws_client, auth_headers):
        """Test refreshing health events"""
        with patch('boto3.client', return_value=mock_aws_client):
            response = client.post(f'/aws/configurations/{test_config.id}/health/refresh',
                                 headers=auth_headers)
            assert response.status_code == 200
            result = json.loads(response.data)
            assert len(result['events']) == 1

class TestEC2Routes:
    """Test EC2 instance routes"""
    
    def test_list_ec2_instances(self, client, test_config, mock_aws_client, auth_headers):
        """Test listing EC2 instances"""
        with patch('boto3.client', return_value=mock_aws_client):
            response = client.get(f'/aws/configurations/{test_config.id}/ec2',
                                headers=auth_headers)
            assert response.status_code == 200
            assert b'test-instance' in response.data
            
    def test_sync_ec2_instances(self, client, test_config, mock_aws_client, auth_headers):
        """Test syncing EC2 instances"""
        with patch('boto3.client', return_value=mock_aws_client):
            response = client.post(f'/aws/configurations/{test_config.id}/ec2/sync',
                                 headers=auth_headers)
            assert response.status_code == 200
            result = json.loads(response.data)
            assert 'instance_count' in result
            
    def test_launch_ec2_instance(self, client, test_config, mock_aws_client, auth_headers):
        """Test launching EC2 instance"""
        with patch('boto3.client', return_value=mock_aws_client):
            data = {
                'region': 'us-east-1',
                'template_id': 1
            }
            response = client.post(f'/aws/configurations/{test_config.id}/ec2',
                                 json=data,
                                 headers=auth_headers)
            assert response.status_code == 201

class TestTemplateRoutes:
    """Test EC2 template routes"""
    
    def test_list_templates(self, client, test_config, auth_headers):
        """Test listing templates"""
        response = client.get(f'/aws/configurations/{test_config.id}/templates',
                            headers=auth_headers)
        assert response.status_code == 200
        
    def test_create_template(self, client, test_config, auth_headers):
        """Test creating template"""
        data = {
            'name': 'test-template',
            'instance_type': 't2.micro',
            'ami_id': 'ami-1234567890abcdef0'
        }
        response = client.post(f'/aws/configurations/{test_config.id}/templates',
                             json=data,
                             headers=auth_headers)
        assert response.status_code == 201
        result = json.loads(response.data)
        assert result['name'] == 'test-template'

class TestSecurityGroupRoutes:
    """Test security group routes"""
    
    def test_list_security_groups(self, client, test_config, mock_aws_client, auth_headers):
        """Test listing security groups"""
        with patch('boto3.client', return_value=mock_aws_client):
            response = client.get(f'/aws/configurations/{test_config.id}/security-groups',
                                headers=auth_headers)
            assert response.status_code == 200
            assert b'test-group' in response.data
            
    def test_create_security_group(self, client, test_config, mock_aws_client, auth_headers):
        """Test creating security group"""
        with patch('boto3.client', return_value=mock_aws_client):
            data = {
                'name': 'new-group',
                'description': 'Test group',
                'vpc_id': 'vpc-1234567890abcdef0',
                'region': 'us-east-1'
            }
            response = client.post(f'/aws/configurations/{test_config.id}/security-groups',
                                 json=data,
                                 headers=auth_headers)
            assert response.status_code == 201
            result = json.loads(response.data)
            assert result['group_name'] == 'new-group'

class TestIAMRoutes:
    """Test IAM user routes"""
    
    def test_list_iam_users(self, client, test_config, mock_aws_client, auth_headers):
        """Test listing IAM users"""
        with patch('boto3.client', return_value=mock_aws_client):
            response = client.get(f'/aws/configurations/{test_config.id}/iam',
                                headers=auth_headers)
            assert response.status_code == 200
            assert b'test-user' in response.data
            
    def test_create_iam_user(self, client, test_config, mock_aws_client, auth_headers):
        """Test creating IAM user"""
        with patch('boto3.client', return_value=mock_aws_client):
            data = {
                'username': 'new-user',
                'create_access_key': True
            }
            response = client.post(f'/aws/configurations/{test_config.id}/iam',
                                 json=data,
                                 headers=auth_headers)
            assert response.status_code == 201
            result = json.loads(response.data)
            assert result['username'] == 'new-user'
            assert 'access_key' in result
            
    def test_rotate_access_key(self, client, test_config, mock_aws_client, auth_headers):
        """Test rotating access key"""
        with patch('boto3.client', return_value=mock_aws_client):
            response = client.post(
                f'/aws/configurations/{test_config.id}/iam/test-user/rotate-key',
                headers=auth_headers
            )
            assert response.status_code == 200
            result = json.loads(response.data)
            assert 'AccessKeyId' in result

@pytest.mark.integration
class TestRouteIntegration:
    """Integration tests for routes"""
    
    def test_full_configuration_lifecycle(self, client, mock_vault, auth_headers):
        """Test complete configuration lifecycle"""
        with patch('vault_utility.VaultUtility', return_value=mock_vault):
            # Create configuration
            create_data = {
                'name': 'lifecycle-test',
                'regions': ['us-east-1'],
                'access_key': 'test-key',
                'secret_key': 'test-secret'
            }
            response = client.post('/aws/configurations',
                                 json=create_data,
                                 headers=auth_headers)
            assert response.status_code == 201
            result = json.loads(response.data)
            config_id = result['id']
            
            # Get configuration
            response = client.get('/aws/configurations', headers=auth_headers)
            assert response.status_code == 200
            assert b'lifecycle-test' in response.data
            
            # Delete configuration
            response = client.delete(f'/aws/configurations/{config_id}',
                                   headers=auth_headers)
            assert response.status_code == 204
            
            # Verify deletion
            response = client.get('/aws/configurations', headers=auth_headers)
            assert b'lifecycle-test' not in response.data
    
    def test_security_group_with_rules(self, client, test_config, mock_aws_client, auth_headers):
        """Test security group creation with rules"""
        with patch('boto3.client', return_value=mock_aws_client):
            # Create security group
            group_data = {
                'name': 'web-server',
                'description': 'Web server security group',
                'vpc_id': 'vpc-1234567890abcdef0',
                'region': 'us-east-1'
            }
            response = client.post(
                f'/aws/configurations/{test_config.id}/security-groups',
                json=group_data,
                headers=auth_headers
            )
            assert response.status_code == 201
            group = json.loads(response.data)
            
            # Add rules
            rules_data = {
                'rules': [{
                    'IpProtocol': 'tcp',
                    'FromPort': 80,
                    'ToPort': 80,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                }],
                'rule_type': 'ingress',
                'region': 'us-east-1'
            }
            response = client.post(
                f'/aws/configurations/{test_config.id}/security-groups/{group["group_id"]}/rules',
                json=rules_data,
                headers=auth_headers
            )
            assert response.status_code == 200
            
            # Verify rules
            response = client.get(
                f'/aws/configurations/{test_config.id}/security-groups/{group["group_id"]}',
                query_string={'region': 'us-east-1'},
                headers=auth_headers
            )
            assert response.status_code == 200
            result = json.loads(response.data)
            assert len(result['inbound_rules']) == 1
