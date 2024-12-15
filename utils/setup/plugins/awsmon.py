"""
AWS Monitoring plugin setup module
"""
from app.extensions import db
from app.plugins.awsmon.models import AWSCredential, SyntheticTest, AWSRegion, EC2Instance, JumpServerTemplate, TestResult, ChangeLog
from utils.setup.plugin_setup import PluginSetup

class AwsmonSetup(PluginSetup):
    """Handle AWS monitoring plugin initialization"""
    
    def init_data(self):
        """Initialize AWS monitoring data"""
        # Create tables first
        for model in [AWSRegion, EC2Instance, JumpServerTemplate, SyntheticTest, TestResult, AWSCredential, ChangeLog]:
            model.__table__.create(db.engine, checkfirst=True)
        
        admin = db.session.query(db.models.User).filter_by(username='admin').first()
        
        # Initialize AWS regions
        default_regions = [
            ('US East (N. Virginia)', 'us-east-1'),
            ('US East (Ohio)', 'us-east-2'),
            ('US West (N. California)', 'us-west-1'),
            ('US West (Oregon)', 'us-west-2'),
            ('Europe (Ireland)', 'eu-west-1'),
            ('Europe (London)', 'eu-west-2'),
            ('Asia Pacific (Tokyo)', 'ap-northeast-1'),
            ('Asia Pacific (Seoul)', 'ap-northeast-2'),
            ('Asia Pacific (Singapore)', 'ap-southeast-1'),
            ('Asia Pacific (Sydney)', 'ap-southeast-2')
        ]
        
        for name, code in default_regions:
            region = AWSRegion.query.filter_by(code=code).first()
            if not region:
                region = AWSRegion(name=name, code=code)
                db.session.add(region)
        
        db.session.commit()  # Commit regions first to get IDs
        
        # Initialize default AWS credential entry (without actual credentials)
        cred = AWSCredential.query.filter_by(name='Default').first()
        if not cred:
            cred = AWSCredential(
                name='Default',
                vault_path='aws/default',
                regions=['us-east-1']  # Default region
            )
            db.session.add(cred)
            db.session.flush()  # Flush to get the ID
            
            # Try to store empty credentials in vault
            try:
                from app.plugins.awsmon.vault_utils import vault_manager
                vault_manager.store_aws_credentials(
                    cred.id,
                    {
                        'aws_access_key_id': '',
                        'aws_secret_access_key': ''
                    }
                )
            except Exception as e:
                print(f"Warning: Failed to store AWS credentials in vault: {e}")
                print("You may need to manually add credentials later")
        
        # Get the first region for the synthetic test
        first_region = AWSRegion.query.first()
        if first_region:
            # Create a dummy EC2 instance for the synthetic test
            instance = EC2Instance.query.filter_by(instance_id='i-example').first()
            if not instance:
                instance = EC2Instance(
                    instance_id='i-example',
                    name='Example Instance',
                    region_id=first_region.id,
                    instance_type='t2.micro',
                    state='running',
                    is_jump_server=True
                )
                db.session.add(instance)
                db.session.flush()  # Flush to get the ID
            
            # Initialize example synthetic test
            test = SyntheticTest.query.filter_by(name='Example Test').first()
            if not test:
                test = SyntheticTest(
                    name='Example Test',
                    test_type='http',
                    target='https://example.com',
                    frequency=300,  # 5 minutes
                    timeout=30,
                    enabled=False,  # Disabled by default
                    instance_id=instance.id,
                    parameters={'expected_status': 200}
                )
                db.session.add(test)
    
    def init_navigation(self):
        """Initialize AWS monitoring navigation"""
        # Add monitoring dashboard to main navigation
        self.add_route(
            page_name='AWS Monitor',
            route='/awsmon/dashboard',
            icon='fa-cloud',
            category_id=self.main_category.id,
            weight=60,
            roles=['user']  # Available to all users
        )
        
        # Add synthetic monitoring page
        self.add_route(
            page_name='Synthetic Checks',
            route='/awsmon/synthetic',
            icon='fa-heartbeat',
            category_id=self.main_category.id,
            weight=61,
            roles=['user']
        )
        
        # Add AWS settings page to admin section
        self.add_route(
            page_name='AWS Settings',
            route='/awsmon/settings',
            icon='fa-cog',
            category_id=self.admin_category.id,
            weight=60,
            roles=['admin']  # Admin only
        )
