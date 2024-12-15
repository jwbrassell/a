"""Unit tests for AWS Monitor plugin."""
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from app.plugins.awsmon import plugin
from app.plugins.awsmon.models import (
    AWSRegion, EC2Instance, SyntheticTest,
    TestResult, JumpServerTemplate, AWSCredential
)
from app.extensions import db

@pytest.fixture
def app_with_awsmon(app):
    """Fixture to initialize app with AWS Monitor plugin."""
    plugin.init_app(app)
    return app

@pytest.fixture
def test_region(app_with_awsmon):
    """Fixture to create a test AWS region."""
    region = AWSRegion(
        name="US East 1",
        code="us-east-1",
        created_by=1
    )
    db.session.add(region)
    db.session.commit()
    yield region
    db.session.delete(region)
    db.session.commit()

@pytest.fixture
def test_instance(app_with_awsmon, test_region):
    """Fixture to create a test EC2 instance."""
    instance = EC2Instance(
        instance_id="i-1234567890abcdef0",
        name="Test Instance",
        region_id=test_region.id,
        instance_type="t2.micro",
        state="running",
        created_by=1
    )
    db.session.add(instance)
    db.session.commit()
    yield instance
    db.session.delete(instance)
    db.session.commit()

@pytest.fixture
def test_template(app_with_awsmon):
    """Fixture to create a test jump server template."""
    template = JumpServerTemplate(
        name="Test Template",
        ami_id="ami-12345678",
        instance_type="t2.micro",
        security_groups=["default"],
        created_by=1
    )
    db.session.add(template)
    db.session.commit()
    yield template
    db.session.delete(template)
    db.session.commit()

@pytest.fixture
def test_synthetic(app_with_awsmon, test_instance):
    """Fixture to create a test synthetic test."""
    test = SyntheticTest(
        name="Test Ping",
        test_type="ping",
        target="8.8.8.8",
        instance_id=test_instance.id,
        created_by=1
    )
    db.session.add(test)
    db.session.commit()
    yield test
    db.session.delete(test)
    db.session.commit()

def test_plugin_initialization(app_with_awsmon):
    """Test plugin initialization and metadata."""
    assert plugin.metadata.name == "AWS Monitor"
    assert plugin.metadata.version == "1.0.0"
    assert "awsmon_dashboard_access" in plugin.metadata.permissions
    assert plugin.blueprint.url_prefix == "/awsmon"

def test_region_model(app_with_awsmon, test_region):
    """Test AWS Region model."""
    assert test_region.name == "US East 1"
    assert test_region.code == "us-east-1"
    assert test_region.created_by == 1
    assert isinstance(test_region.created_at, datetime)

def test_instance_model(app_with_awsmon, test_instance, test_region):
    """Test EC2 Instance model."""
    assert test_instance.name == "Test Instance"
    assert test_instance.region_id == test_region.id
    assert test_instance.instance_type == "t2.micro"
    assert test_instance.created_by == 1
    assert isinstance(test_instance.created_at, datetime)

def test_template_model(app_with_awsmon, test_template):
    """Test Jump Server Template model."""
    assert test_template.name == "Test Template"
    assert test_template.ami_id == "ami-12345678"
    assert test_template.instance_type == "t2.micro"
    assert test_template.created_by == 1
    assert isinstance(test_template.created_at, datetime)

def test_synthetic_model(app_with_awsmon, test_synthetic, test_instance):
    """Test Synthetic Test model."""
    assert test_synthetic.name == "Test Ping"
    assert test_synthetic.test_type == "ping"
    assert test_synthetic.target == "8.8.8.8"
    assert test_synthetic.instance_id == test_instance.id
    assert test_synthetic.created_by == 1
    assert isinstance(test_synthetic.created_at, datetime)

@pytest.mark.parametrize("endpoint,method,expected_status", [
    ("/awsmon/", "GET", 200),
    ("/awsmon/instances", "GET", 200),
    ("/awsmon/synthetic", "GET", 200),
    ("/awsmon/templates", "GET", 200),
    ("/awsmon/settings", "GET", 200),
])
def test_route_access(client, app_with_awsmon, endpoint, method, expected_status):
    """Test route accessibility."""
    with patch('app.utils.enhanced_rbac.requires_permission'):
        response = client.open(endpoint, method=method)
        assert response.status_code == expected_status

@pytest.mark.parametrize("permission", [
    "awsmon_dashboard_access",
    "awsmon_instances_access",
    "awsmon_synthetic_access",
    "awsmon_templates_access",
    "awsmon_settings_access",
])
def test_permissions_registered(app_with_awsmon, permission):
    """Test that permissions are properly registered."""
    from app.models.permissions import Permission
    assert Permission.query.filter_by(name=permission).first() is not None

def test_instance_api(client, app_with_awsmon, test_instance):
    """Test instance API endpoints."""
    with patch('app.utils.enhanced_rbac.requires_permission'):
        # List instances
        response = client.get("/awsmon/api/instances")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert len(data["data"]) > 0
        
        # Instance action
        response = client.post(f"/awsmon/api/instances/{test_instance.instance_id}/action", 
                             json={"action": "stop"})
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"

def test_synthetic_api(client, app_with_awsmon, test_synthetic):
    """Test synthetic testing API endpoints."""
    with patch('app.utils.enhanced_rbac.requires_permission'):
        # List tests
        response = client.get("/awsmon/api/synthetic/tests")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert len(data["data"]) > 0
        
        # Get test results
        response = client.get("/awsmon/api/synthetic/results")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"

def test_template_api(client, app_with_awsmon, test_template):
    """Test template API endpoints."""
    with patch('app.utils.enhanced_rbac.requires_permission'):
        # List templates
        response = client.get("/awsmon/api/templates")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert len(data["data"]) > 0
        
        # Get template details
        response = client.get(f"/awsmon/api/templates/{test_template.id}")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert data["data"]["name"] == test_template.name

def test_soft_delete(app_with_awsmon, test_instance):
    """Test soft delete functionality."""
    # Soft delete instance
    test_instance.deleted_at = datetime.utcnow()
    db.session.commit()
    
    # Verify instance is not returned in active queries
    instances = EC2Instance.query.filter_by(deleted_at=None).all()
    assert test_instance not in instances

def test_user_tracking(app_with_awsmon, test_instance):
    """Test user tracking fields."""
    # Update instance
    test_instance.updated_by = 2
    test_instance.state = "stopped"
    db.session.commit()
    
    # Verify tracking fields
    assert test_instance.created_by == 1
    assert test_instance.updated_by == 2
    assert isinstance(test_instance.updated_at, datetime)
    assert test_instance.updated_at > test_instance.created_at

def test_template_rendering(client, app_with_awsmon):
    """Test template rendering."""
    with patch('app.utils.enhanced_rbac.requires_permission'):
        response = client.get("/awsmon/")
        assert response.status_code == 200
        assert b"AWS Monitor" in response.data
