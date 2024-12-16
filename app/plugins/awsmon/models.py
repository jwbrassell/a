"""AWS Monitor models."""
from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict

class EC2Instance(db.Model):
    """EC2 Instance model."""
    __tablename__ = 'aws_instances'

    id = db.Column(db.Integer, primary_key=True)
    instance_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100))
    instance_type = db.Column(db.String(20))
    state = db.Column(db.String(20))
    region_id = db.Column(db.Integer, db.ForeignKey('aws_regions.id'))
    public_ip = db.Column(db.String(15))
    private_ip = db.Column(db.String(15))
    is_jump_server = db.Column(db.Boolean, default=False)
    tags = db.Column(MutableDict.as_mutable(JSONB))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    deleted_at = db.Column(db.DateTime)

    region = db.relationship('AWSRegion', backref='instances')

class AWSRegion(db.Model):
    """AWS Region model."""
    __tablename__ = 'aws_regions'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100))
    enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

class SyntheticTest(db.Model):
    """Synthetic Test model."""
    __tablename__ = 'aws_synthetic_tests'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    test_type = db.Column(db.String(20), nullable=False)  # ping, traceroute, port_check, http
    target = db.Column(db.String(255), nullable=False)
    instance_id = db.Column(db.Integer, db.ForeignKey('aws_instances.id'))
    frequency = db.Column(db.Integer, default=60)  # seconds
    timeout = db.Column(db.Integer, default=5)  # seconds
    parameters = db.Column(MutableDict.as_mutable(JSONB))
    enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    deleted_at = db.Column(db.DateTime)

    instance = db.relationship('EC2Instance', backref='synthetic_tests')

class TestResult(db.Model):
    """Test Result model."""
    __tablename__ = 'aws_test_results'

    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('aws_synthetic_tests.id'))
    instance_id = db.Column(db.Integer, db.ForeignKey('aws_instances.id'))
    status = db.Column(db.String(20))  # success, failure
    response_time = db.Column(db.Float)  # milliseconds
    error_message = db.Column(db.Text)
    details = db.Column(MutableDict.as_mutable(JSONB))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))

    test = db.relationship('SyntheticTest', backref='results')
    instance = db.relationship('EC2Instance', backref='test_results')

class JumpServerTemplate(db.Model):
    """Jump Server Template model."""
    __tablename__ = 'aws_jump_server_templates'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    ami_id = db.Column(db.String(50), nullable=False)
    instance_type = db.Column(db.String(20), nullable=False)
    security_groups = db.Column(db.ARRAY(db.String))
    user_data = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    deleted_at = db.Column(db.DateTime)

class ChangeLog(db.Model):
    """Change Log model for tracking AWS resource changes."""
    __tablename__ = 'aws_change_log'

    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(50), nullable=False)  # start, stop, terminate, etc.
    resource_type = db.Column(db.String(50), nullable=False)  # instance, template, etc.
    resource_id = db.Column(db.String(50), nullable=False)
    details = db.Column(MutableDict.as_mutable(JSONB))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

def init_models():
    """Initialize models."""
    # Add default regions if they don't exist
    default_regions = [
        ('us-east-1', 'US East (N. Virginia)'),
        ('us-west-2', 'US West (Oregon)'),
        ('eu-west-1', 'EU (Ireland)'),
        ('ap-southeast-1', 'Asia Pacific (Singapore)')
    ]
    
    for code, name in default_regions:
        if not AWSRegion.query.filter_by(code=code).first():
            region = AWSRegion(code=code, name=name)
            db.session.add(region)
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e
