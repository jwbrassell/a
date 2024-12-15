import hvac
from flask import current_app
import json
from datetime import datetime
from app.extensions import db
from app.plugins.awsmon.models import AWSCredential, ChangeLog

class AWSVaultManager:
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app

    def get_vault_client(self):
        """Get authenticated Vault client"""
        return hvac.Client(
            url=current_app.config['VAULT_ADDR'],
            token=current_app.config['VAULT_TOKEN']
        )

    def store_credentials(self, name, access_key, secret_key, regions):
        """Store AWS credentials in Vault"""
        try:
            client = self.get_vault_client()
            
            # Generate Vault path
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            vault_path = f'aws/credentials/{name}_{timestamp}'
            
            # Store credentials in Vault
            client.secrets.kv.v2.create_or_update_secret(
                path=vault_path,
                secret={
                    'access_key': access_key,
                    'secret_key': secret_key
                }
            )
            
            # Create database record
            credential = AWSCredential(
                name=name,
                vault_path=vault_path,
                regions=regions
            )
            db.session.add(credential)
            
            # Log the change
            log = ChangeLog(
                action='create',
                resource_type='credential',
                resource_id=name,
                details={'regions': regions}
            )
            db.session.add(log)
            
            db.session.commit()
            
            return credential
            
        except Exception as e:
            current_app.logger.error(f"Error storing AWS credentials: {str(e)}")
            db.session.rollback()
            raise

    def update_credentials(self, credential_id, access_key=None, secret_key=None, regions=None):
        """Update existing AWS credentials"""
        try:
            client = self.get_vault_client()
            credential = AWSCredential.query.get(credential_id)
            
            if not credential:
                raise ValueError(f"No credential found with ID {credential_id}")
            
            # Get current credentials from Vault
            current_creds = client.secrets.kv.v2.read_secret_version(
                path=credential.vault_path
            )['data']['data']
            
            # Update credentials in Vault
            client.secrets.kv.v2.create_or_update_secret(
                path=credential.vault_path,
                secret={
                    'access_key': access_key or current_creds['access_key'],
                    'secret_key': secret_key or current_creds['secret_key']
                }
            )
            
            # Update regions if provided
            if regions is not None:
                credential.regions = regions
            
            # Log the change
            log = ChangeLog(
                action='update',
                resource_type='credential',
                resource_id=credential.name,
                details={
                    'updated_fields': [
                        'access_key' if access_key else None,
                        'secret_key' if secret_key else None,
                        'regions' if regions else None
                    ]
                }
            )
            db.session.add(log)
            
            db.session.commit()
            
            return credential
            
        except Exception as e:
            current_app.logger.error(f"Error updating AWS credentials: {str(e)}")
            db.session.rollback()
            raise

    def delete_credentials(self, credential_id):
        """Delete AWS credentials from Vault and database"""
        try:
            client = self.get_vault_client()
            credential = AWSCredential.query.get(credential_id)
            
            if not credential:
                raise ValueError(f"No credential found with ID {credential_id}")
            
            # Delete from Vault
            client.secrets.kv.v2.delete_metadata_and_all_versions(
                path=credential.vault_path
            )
            
            # Log the change
            log = ChangeLog(
                action='delete',
                resource_type='credential',
                resource_id=credential.name,
                details={'regions': credential.regions}
            )
            db.session.add(log)
            
            # Delete from database
            db.session.delete(credential)
            db.session.commit()
            
        except Exception as e:
            current_app.logger.error(f"Error deleting AWS credentials: {str(e)}")
            db.session.rollback()
            raise

    def validate_credentials(self, access_key, secret_key, region='us-east-1'):
        """Validate AWS credentials by attempting to list EC2 instances"""
        import boto3
        try:
            session = boto3.Session(
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region
            )
            
            # Try to list EC2 instances
            ec2 = session.client('ec2')
            ec2.describe_instances(MaxResults=5)
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"AWS credential validation failed: {str(e)}")
            return False

    def rotate_credentials(self, credential_id):
        """Rotate AWS credentials using IAM"""
        try:
            client = self.get_vault_client()
            credential = AWSCredential.query.get(credential_id)
            
            if not credential:
                raise ValueError(f"No credential found with ID {credential_id}")
            
            # Get current credentials
            current_creds = client.secrets.kv.v2.read_secret_version(
                path=credential.vault_path
            )['data']['data']
            
            # Create IAM session
            session = boto3.Session(
                aws_access_key_id=current_creds['access_key'],
                aws_secret_access_key=current_creds['secret_key']
            )
            iam = session.client('iam')
            
            # Create new access key
            response = iam.create_access_key()
            new_access_key = response['AccessKey']
            
            # Validate new credentials
            if not self.validate_credentials(
                new_access_key['AccessKeyId'],
                new_access_key['SecretAccessKey']
            ):
                raise Exception("New credentials validation failed")
            
            # Store new credentials
            self.update_credentials(
                credential_id,
                access_key=new_access_key['AccessKeyId'],
                secret_key=new_access_key['SecretAccessKey']
            )
            
            # Delete old access key
            iam.delete_access_key(
                AccessKeyId=current_creds['access_key']
            )
            
            # Log the rotation
            log = ChangeLog(
                action='rotate',
                resource_type='credential',
                resource_id=credential.name,
                details={'timestamp': datetime.utcnow().isoformat()}
            )
            db.session.add(log)
            db.session.commit()
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error rotating AWS credentials: {str(e)}")
            db.session.rollback()
            raise

    def get_credentials(self, credential_id):
        """Get AWS credentials from Vault"""
        try:
            client = self.get_vault_client()
            credential = AWSCredential.query.get(credential_id)
            
            if not credential:
                raise ValueError(f"No credential found with ID {credential_id}")
            
            # Get credentials from Vault
            response = client.secrets.kv.v2.read_secret_version(
                path=credential.vault_path
            )
            
            return response['data']['data']
            
        except Exception as e:
            current_app.logger.error(f"Error retrieving AWS credentials: {str(e)}")
            raise

    def test_vault_connection(self):
        """Test Vault connection and authentication"""
        try:
            client = self.get_vault_client()
            return client.is_authenticated()
        except Exception as e:
            current_app.logger.error(f"Vault connection test failed: {str(e)}")
            return False

# Create vault manager instance
vault_manager = AWSVaultManager()
