"""AWS Monitor plugin models."""
from datetime import datetime
from app.extensions import db
from sqlalchemy.dialects.mysql import JSON

class AWSRegion(db.Model):
    """AWS Region model for managing monitored regions."""
    __tablename__ = 'awsmon_regions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    code = db.Column(db.String(20), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    deleted_at = db.Column(db.DateTime)
    
    # Relationships
    instances = db.relationship('EC2Instance', backref='region', lazy=True)
    creator = db.relationship('User', foreign_keys=[created_by])
    updater = db.relationship('User', foreign_keys=[updated_by])

class EC2Instance(db.Model):
    """EC2 Instance model for tracking AWS instances."""
    __tablename__ = 'awsmon_instances'
    
    id = db.Column(db.Integer, primary_key=True)
    instance_id = db.Column(db.String(50), nullable=False, unique=True)
    name = db.Column(db.String(100))
    region_id = db.Column(db.Integer, db.ForeignKey('awsmon_regions.id'), nullable=False)
    instance_type = db.Column(db.String(20))
    state = db.Column(db.String(20))
    public_ip = db.Column(db.String(15))
    private_ip = db.Column(db.String(15))
    launch_time = db.Column(db.DateTime)
    tags = db.Column(JSON)
    is_jump_server = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    deleted_at = db.Column(db.DateTime)
    
    # Relationships
    synthetic_tests = db.relationship('SyntheticTest', backref='instance', lazy=True)
    test_results = db.relationship('TestResult', backref='instance', lazy=True)
    creator = db.relationship('User', foreign_keys=[created_by])
    updater = db.relationship('User', foreign_keys=[updated_by])

class JumpServerTemplate(db.Model):
    """Template model for jump server configuration."""
    __tablename__ = 'awsmon_jump_server_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    ami_id = db.Column(db.String(20), nullable=False)
    instance_type = db.Column(db.String(20), nullable=False)
    security_groups = db.Column(JSON)
    user_data = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    deleted_at = db.Column(db.DateTime)
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[created_by])
    updater = db.relationship('User', foreign_keys=[updated_by])

class SyntheticTest(db.Model):
    """Model for synthetic monitoring tests."""
    __tablename__ = 'awsmon_synthetic_tests'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    test_type = db.Column(db.String(20), nullable=False)  # ping, traceroute, port_check, http
    target = db.Column(db.String(255), nullable=False)  # IP, hostname, or URL
    frequency = db.Column(db.Integer, default=60)  # seconds
    timeout = db.Column(db.Integer, default=5)  # seconds
    enabled = db.Column(db.Boolean, default=True)
    instance_id = db.Column(db.Integer, db.ForeignKey('awsmon_instances.id'), nullable=False)
    parameters = db.Column(JSON)  # Additional test parameters
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    deleted_at = db.Column(db.DateTime)
    
    # Relationships
    results = db.relationship('TestResult', backref='test', lazy=True)
    creator = db.relationship('User', foreign_keys=[created_by])
    updater = db.relationship('User', foreign_keys=[updated_by])

class TestResult(db.Model):
    """Model for storing synthetic test results."""
    __tablename__ = 'awsmon_test_results'
    
    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('awsmon_synthetic_tests.id'), nullable=False)
    instance_id = db.Column(db.Integer, db.ForeignKey('awsmon_instances.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # success, failure, timeout
    response_time = db.Column(db.Float)  # milliseconds
    error_message = db.Column(db.Text)
    details = db.Column(JSON)  # Test-specific details (traceroute hops, HTTP response, etc)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[created_by])

class AWSCredential(db.Model):
    """Model for storing AWS credential references in Vault."""
    __tablename__ = 'awsmon_credentials'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    vault_path = db.Column(db.String(255), nullable=False, unique=True)
    regions = db.Column(JSON)  # List of enabled regions
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    deleted_at = db.Column(db.DateTime)
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[created_by])
    updater = db.relationship('User', foreign_keys=[updated_by])

class ChangeLog(db.Model):
    """Model for tracking changes to AWS resources."""
    __tablename__ = 'awsmon_changelog'
    
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(50), nullable=False)  # create, update, delete, start, stop
    resource_type = db.Column(db.String(50), nullable=False)  # instance, test, template
    resource_id = db.Column(db.String(50), nullable=False)
    details = db.Column(JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[created_by])
