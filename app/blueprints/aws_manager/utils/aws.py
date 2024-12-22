"""
AWS Manager Utilities
------------------
Core AWS management functionality and helper functions.
"""

from flask import abort
from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
from ..models import AWSConfiguration, EC2Instance, AWSHealthEvent
from app.extensions import db
from vault_utility import VaultUtility
import boto3
from botocore.config import Config

def get_aws_manager(config_id: int) -> 'AWSManager':
    """Helper to get AWS manager instance from configuration"""
    config = AWSConfiguration.query.get_or_404(config_id)
    vault = VaultUtility()
    credentials = vault.get_secret(config.vault_path)
    if not credentials:
        abort(404, description="AWS credentials not found in vault")
    
    return AWSManager(
        access_key=credentials['access_key'],
        secret_key=credentials['secret_key'],
        regions=config.regions,
        verify_ssl=True  # Can be made configurable if needed
    )

class AWSManager:
    """Manages AWS operations across multiple regions"""
    
    def __init__(self, access_key: str, secret_key: str, regions: List[str], verify_ssl: bool = True):
        self.access_key = access_key
        self.secret_key = secret_key
        self.regions = regions
        self.verify_ssl = verify_ssl
        self._clients = {}
        
        # Configure boto3 with SSL verification settings
        self.boto_config = Config(
            verify=verify_ssl,
            retries={'max_attempts': 3}
        )

    def _get_client(self, service: str, region: str) -> Any:
        """Get or create a boto3 client for the specified service and region"""
        key = f"{service}_{region}"
        if key not in self._clients:
            self._clients[key] = boto3.client(
                service,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=region,
                config=self.boto_config
            )
        return self._clients[key]

    # IAM User Operations
    def get_iam_users(self) -> List[Dict]:
        """Get IAM users (IAM is global, so we only need to query once)"""
        iam = self._get_client('iam', self.regions[0])
        users = []
        
        paginator = iam.get_paginator('list_users')
        for page in paginator.paginate():
            for user in page['Users']:
                user_data = {
                    'username': user['UserName'],
                    'user_id': user['UserId'],
                    'arn': user['Arn'],
                    'created_date': user['CreateDate'].isoformat(),
                }
                # Get user's groups
                groups_response = iam.list_groups_for_user(UserName=user['UserName'])
                user_data['groups'] = [g['GroupName'] for g in groups_response['Groups']]
                users.append(user_data)
                
        return users

    def get_iam_user_details(self, username: str) -> Dict:
        """Get detailed information about an IAM user"""
        iam = self._get_client('iam', self.regions[0])
        
        # Get access keys
        keys_response = iam.list_access_keys(UserName=username)
        access_keys = []
        for key in keys_response['AccessKeyMetadata']:
            access_keys.append({
                'AccessKeyId': key['AccessKeyId'],
                'Status': key['Status'],
                'CreateDate': key['CreateDate'].isoformat()
            })
        
        # Get attached policies
        policies = []
        attached_policies = iam.list_attached_user_policies(UserName=username)
        for policy in attached_policies['AttachedPolicies']:
            policy_details = iam.get_policy(PolicyArn=policy['PolicyArn'])['Policy']
            policies.append({
                'PolicyName': policy['PolicyName'],
                'PolicyArn': policy['PolicyArn'],
                'PolicyType': 'AWS Managed' if 'aws-managed' in policy['PolicyArn'] else 'Customer Managed'
            })
        
        # Get groups with details
        groups_response = iam.list_groups_for_user(UserName=username)
        groups = []
        for group in groups_response['Groups']:
            groups.append({
                'GroupName': group['GroupName'],
                'GroupArn': group['Arn'],
                'CreateDate': group['CreateDate'].isoformat()
            })
        
        return {
            'access_keys': access_keys,
            'policies': policies,
            'groups': groups
        }

    def create_iam_user(self, username: str, create_access_key: bool = True) -> Dict:
        """Create a new IAM user"""
        iam = self._get_client('iam', self.regions[0])
        try:
            # Create user
            user = iam.create_user(UserName=username)['User']
            
            result = {
                'username': user['UserName'],
                'user_id': user['UserId'],
                'arn': user['Arn'],
                'created_date': user['CreateDate'].isoformat()
            }
            
            # Create access key if requested
            if create_access_key:
                access_key = iam.create_access_key(UserName=username)['AccessKey']
                result['access_key'] = {
                    'AccessKeyId': access_key['AccessKeyId'],
                    'SecretAccessKey': access_key['SecretAccessKey']
                }
            
            return result
        except Exception as e:
            raise

    def delete_iam_user(self, username: str) -> bool:
        """Delete an IAM user"""
        iam = self._get_client('iam', self.regions[0])
        try:
            # First, remove all access keys
            keys = iam.list_access_keys(UserName=username)['AccessKeyMetadata']
            for key in keys:
                iam.delete_access_key(
                    UserName=username,
                    AccessKeyId=key['AccessKeyId']
                )
            
            # Remove from all groups
            groups = iam.list_groups_for_user(UserName=username)['Groups']
            for group in groups:
                iam.remove_user_from_group(
                    GroupName=group['GroupName'],
                    UserName=username
                )
            
            # Detach all policies
            policies = iam.list_attached_user_policies(UserName=username)['AttachedPolicies']
            for policy in policies:
                iam.detach_user_policy(
                    UserName=username,
                    PolicyArn=policy['PolicyArn']
                )
            
            # Finally, delete the user
            iam.delete_user(UserName=username)
            return True
        except Exception as e:
            raise

    def rotate_access_key(self, username: str) -> Dict:
        """Create a new access key and deactivate the old one"""
        iam = self._get_client('iam', self.regions[0])
        try:
            # List existing keys
            existing_keys = iam.list_access_keys(UserName=username)['AccessKeyMetadata']
            
            # Create new key
            new_key = iam.create_access_key(UserName=username)['AccessKey']
            
            # Deactivate old keys
            for key in existing_keys:
                iam.update_access_key(
                    UserName=username,
                    AccessKeyId=key['AccessKeyId'],
                    Status='Inactive'
                )
            
            return {
                'AccessKeyId': new_key['AccessKeyId'],
                'SecretAccessKey': new_key['SecretAccessKey'],
                'CreateDate': new_key['CreateDate'].isoformat()
            }
        except Exception as e:
            raise

    def attach_user_policy(self, username: str, policy_arn: str) -> bool:
        """Attach a policy to an IAM user"""
        iam = self._get_client('iam', self.regions[0])
        try:
            iam.attach_user_policy(
                UserName=username,
                PolicyArn=policy_arn
            )
            return True
        except Exception as e:
            raise

    def detach_user_policy(self, username: str, policy_arn: str) -> bool:
        """Detach a policy from an IAM user"""
        iam = self._get_client('iam', self.regions[0])
        try:
            iam.detach_user_policy(
                UserName=username,
                PolicyArn=policy_arn
            )
            return True
        except Exception as e:
            raise

    def list_available_policies(self) -> List[Dict]:
        """List available IAM policies"""
        iam = self._get_client('iam', self.regions[0])
        policies = []
        
        # Get AWS managed policies
        paginator = iam.get_paginator('list_policies')
        for page in paginator.paginate(Scope='AWS'):
            for policy in page['Policies']:
                policies.append({
                    'PolicyName': policy['PolicyName'],
                    'PolicyArn': policy['PolicyArn'],
                    'Description': policy.get('Description', ''),
                    'Type': 'AWS Managed'
                })
        
        # Get customer managed policies
        for page in paginator.paginate(Scope='Local'):
            for policy in page['Policies']:
                policies.append({
                    'PolicyName': policy['PolicyName'],
                    'PolicyArn': policy['PolicyArn'],
                    'Description': policy.get('Description', ''),
                    'Type': 'Customer Managed'
                })
        
        return policies

    def list_iam_groups(self) -> List[Dict]:
        """List IAM groups"""
        iam = self._get_client('iam', self.regions[0])
        groups = []
        
        paginator = iam.get_paginator('list_groups')
        for page in paginator.paginate():
            for group in page['Groups']:
                groups.append({
                    'GroupName': group['GroupName'],
                    'GroupId': group['GroupId'],
                    'Arn': group['Arn'],
                    'CreateDate': group['CreateDate'].isoformat()
                })
        
        return groups

    def add_user_to_group(self, username: str, group_name: str) -> bool:
        """Add an IAM user to a group"""
        iam = self._get_client('iam', self.regions[0])
        try:
            iam.add_user_to_group(
                GroupName=group_name,
                UserName=username
            )
            return True
        except Exception as e:
            raise

    def remove_user_from_group(self, username: str, group_name: str) -> bool:
        """Remove an IAM user from a group"""
        iam = self._get_client('iam', self.regions[0])
        try:
            iam.remove_user_from_group(
                GroupName=group_name,
                UserName=username
            )
            return True
        except Exception as e:
            raise

    # Security Group Operations
    def get_security_groups(self, region: Optional[str] = None) -> List[Dict]:
        """Get security groups across all regions or a specific region"""
        security_groups = []
        regions_to_check = [region] if region else self.regions

        for r in regions_to_check:
            ec2 = self._get_client('ec2', r)
            response = ec2.describe_security_groups()
            
            for sg in response['SecurityGroups']:
                sg_data = {
                    'region': r,
                    'group_id': sg['GroupId'],
                    'group_name': sg['GroupName'],
                    'description': sg['Description'],
                    'vpc_id': sg['VpcId'],
                    'inbound_rules': sg['IpPermissions'],
                    'outbound_rules': sg['IpPermissionsEgress']
                }
                security_groups.append(sg_data)

        return security_groups

    def create_security_group(self, region: str, name: str, description: str, vpc_id: str) -> Dict:
        """Create a new security group"""
        ec2 = self._get_client('ec2', region)
        try:
            response = ec2.create_security_group(
                GroupName=name,
                Description=description,
                VpcId=vpc_id
            )
            group_id = response['GroupId']
            
            # Tag the security group
            ec2.create_tags(
                Resources=[group_id],
                Tags=[{'Key': 'Name', 'Value': name}]
            )
            
            return {
                'group_id': group_id,
                'group_name': name,
                'description': description,
                'vpc_id': vpc_id,
                'region': region,
                'inbound_rules': [],
                'outbound_rules': []
            }
        except Exception as e:
            raise

    def delete_security_group(self, region: str, group_id: str) -> bool:
        """Delete a security group"""
        ec2 = self._get_client('ec2', region)
        try:
            ec2.delete_security_group(GroupId=group_id)
            return True
        except Exception as e:
            raise

    def add_security_group_rules(self, region: str, group_id: str, rules: List[Dict], rule_type: str = 'ingress') -> bool:
        """Add rules to a security group"""
        ec2 = self._get_client('ec2', region)
        try:
            if rule_type == 'ingress':
                ec2.authorize_security_group_ingress(
                    GroupId=group_id,
                    IpPermissions=rules
                )
            else:
                ec2.authorize_security_group_egress(
                    GroupId=group_id,
                    IpPermissions=rules
                )
            return True
        except Exception as e:
            raise

    def remove_security_group_rules(self, region: str, group_id: str, rules: List[Dict], rule_type: str = 'ingress') -> bool:
        """Remove rules from a security group"""
        ec2 = self._get_client('ec2', region)
        try:
            if rule_type == 'ingress':
                ec2.revoke_security_group_ingress(
                    GroupId=group_id,
                    IpPermissions=rules
                )
            else:
                ec2.revoke_security_group_egress(
                    GroupId=group_id,
                    IpPermissions=rules
                )
            return True
        except Exception as e:
            raise

    # Health Event Operations
    def get_health_events(self, aws_config_id: int) -> List[Dict]:
        """Get AWS Health events across all regions"""
        health = self._get_client('health', self.regions[0])  # Health API is global
        
        try:
            # Get events from the last 30 days
            start_time = datetime.now(timezone.utc)
            
            response = health.describe_events(
                filter={
                    'startTimes': [{
                        'from': start_time
                    }]
                }
            )
            
            events = []
            for event in response['events']:
                # Get detailed event information
                detail = health.describe_event_details(
                    eventArns=[event['arn']]
                )['successfulSet'][0]['eventDescription']
                
                # Get affected resources
                resources = []
                try:
                    affected = health.describe_affected_entities(
                        filter={'eventArns': [event['arn']]}
                    )
                    resources = [entity['entityValue'] for entity in affected['entities']]
                except Exception:
                    pass  # Some events might not have affected resources
                
                event_data = {
                    'event_arn': event['arn'],
                    'service': event['service'],
                    'event_type_code': event['eventTypeCode'],
                    'event_type_category': event['eventTypeCategory'],
                    'region': event.get('region'),
                    'start_time': event['startTime'],
                    'end_time': event.get('endTime'),
                    'status': event['statusCode'],
                    'affected_resources': resources,
                    'description': detail['latestDescription']
                }
                
                # Create or update event in database
                db_event = AWSHealthEvent.query.filter_by(event_arn=event['arn']).first()
                if db_event:
                    for key, value in event_data.items():
                        setattr(db_event, key, value)
                else:
                    db_event = AWSHealthEvent(aws_config_id=aws_config_id, **event_data)
                    db.session.add(db_event)
                
                events.append(event_data)
            
            db.session.commit()
            return events
            
        except Exception as e:
            db.session.rollback()
            raise

    # EC2 Instance Operations
    def sync_ec2_instances(self, aws_config_id: int) -> List[Dict]:
        """Sync EC2 instances with database"""
        try:
            # Get all current instances
            current_instances = self.get_ec2_instances()['instances']
            
            # Update database
            for instance_data in current_instances:
                db_instance = EC2Instance.query.filter_by(
                    instance_id=instance_data['instance_id']
                ).first()
                
                if db_instance:
                    # Update existing instance
                    db_instance.state = instance_data['state']
                    db_instance.public_ip = instance_data['public_ip']
                    db_instance.private_ip = instance_data['private_ip']
                else:
                    # Create new instance record
                    db_instance = EC2Instance(
                        aws_config_id=aws_config_id,
                        instance_id=instance_data['instance_id'],
                        region=instance_data['region'],
                        instance_type=instance_data['instance_type'],
                        state=instance_data['state'],
                        public_ip=instance_data['public_ip'],
                        private_ip=instance_data['private_ip'],
                        launch_time=datetime.fromisoformat(instance_data['launch_time']),
                        tags=instance_data['tags']
                    )
                    db.session.add(db_instance)
            
            db.session.commit()
            return current_instances
            
        except Exception as e:
            db.session.rollback()
            raise
