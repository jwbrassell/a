"""Test suite for Reports plugin."""

import pytest
from datetime import datetime
from flask import url_for
from app import db
from app.plugins.reports.models import DatabaseConnection, ReportView
from app.models import User, Role

@pytest.fixture
def test_db_connection(test_user):
    """Create a test database connection."""
    connection = DatabaseConnection(
        name="Test DB",
        description="Test database connection",
        db_type="sqlite",
        database=":memory:",
        created_by=test_user.id,
        updated_by=test_user.id
    )
    db.session.add(connection)
    db.session.commit()
    return connection

@pytest.fixture
def test_report_view(test_user, test_db_connection):
    """Create a test report view."""
    view = ReportView(
        title="Test Report",
        description="Test report view",
        database_id=test_db_connection.id,
        query="SELECT 1 as test",
        column_config={
            "test": {
                "label": "Test Column",
                "sortable": True
            }
        },
        created_by=test_user.id,
        updated_by=test_user.id
    )
    db.session.add(view)
    db.session.commit()
    return view

def test_plugin_initialization(app):
    """Test that the plugin initializes correctly."""
    assert 'reports' in app.blueprints
    assert '/reports' in [rule.rule for rule in app.url_map.iter_rules()]

def test_database_connection_model(test_user):
    """Test DatabaseConnection model."""
    connection = DatabaseConnection(
        name="Test Connection",
        description="Test description",
        db_type="sqlite",
        database=":memory:",
        created_by=test_user.id,
        updated_by=test_user.id
    )
    db.session.add(connection)
    db.session.commit()

    assert connection.id is not None
    assert connection.name == "Test Connection"
    assert connection.created_at is not None
    assert connection.updated_at is not None
    assert connection.deleted_at is None
    assert connection.is_active is True

def test_report_view_model(test_user, test_db_connection):
    """Test ReportView model."""
    view = ReportView(
        title="Test View",
        description="Test description",
        database_id=test_db_connection.id,
        query="SELECT 1",
        column_config={"col1": {"label": "Column 1"}},
        created_by=test_user.id,
        updated_by=test_user.id
    )
    db.session.add(view)
    db.session.commit()

    assert view.id is not None
    assert view.title == "Test View"
    assert view.created_at is not None
    assert view.updated_at is not None
    assert view.deleted_at is None

def test_database_routes(client, test_user, admin_role):
    """Test database management routes."""
    # Login
    client.post('/login', data={'username': test_user.username, 'password': 'password'})
    
    # Add admin role to user
    test_user.roles.append(admin_role)
    db.session.commit()

    # Test database list page
    response = client.get('/reports/databases')
    assert response.status_code == 200

    # Test database creation
    response = client.post('/reports/api/database', json={
        'name': 'New DB',
        'description': 'New database',
        'db_type': 'sqlite',
        'database': ':memory:'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['name'] == 'New DB'

    # Test database update
    db_id = data['id']
    response = client.put(f'/reports/api/database/{db_id}', json={
        'name': 'Updated DB'
    })
    assert response.status_code == 200
    assert response.get_json()['name'] == 'Updated DB'

    # Test database deletion
    response = client.delete(f'/reports/api/database/{db_id}')
    assert response.status_code == 204

def test_view_routes(client, test_user, test_db_connection, admin_role):
    """Test report view routes."""
    # Login
    client.post('/login', data={'username': test_user.username, 'password': 'password'})
    
    # Add admin role to user
    test_user.roles.append(admin_role)
    db.session.commit()

    # Test view creation
    response = client.post('/reports/view/new', json={
        'title': 'New View',
        'description': 'New report view',
        'database_id': test_db_connection.id,
        'query': 'SELECT 1',
        'column_config': {'col1': {'label': 'Column 1'}}
    })
    assert response.status_code == 200
    data = response.get_json()
    assert 'redirect' in data

    # Get view ID from redirect URL
    view_id = int(data['redirect'].split('/')[-1])

    # Test view page
    response = client.get(f'/reports/view/{view_id}')
    assert response.status_code == 200

    # Test view update
    response = client.post(f'/reports/view/{view_id}/edit', json={
        'title': 'Updated View',
        'description': 'Updated description',
        'database_id': test_db_connection.id,
        'query': 'SELECT 1',
        'column_config': {'col1': {'label': 'Updated Column'}}
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['title'] == 'Updated View'

    # Test view deletion
    response = client.delete(f'/reports/api/view/{view_id}')
    assert response.status_code == 204

def test_data_routes(client, test_user, test_report_view, admin_role):
    """Test data fetching routes."""
    # Login
    client.post('/login', data={'username': test_user.username, 'password': 'password'})
    
    # Add admin role to user
    test_user.roles.append(admin_role)
    db.session.commit()

    # Test data fetching
    response = client.get(f'/reports/api/view/{test_report_view.id}/data')
    assert response.status_code == 200
    data = response.get_json()
    assert 'data' in data
    assert 'columns' in data

    # Test query testing
    response = client.post('/reports/api/test-query', json={
        'database_id': test_report_view.database_id,
        'query': 'SELECT 1 as test'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert 'columns' in data
    assert 'sample_data' in data

def test_permissions(client, test_user, test_report_view):
    """Test permission restrictions."""
    # Login as user without admin role
    client.post('/login', data={'username': test_user.username, 'password': 'password'})

    # Test database management access (should be denied)
    response = client.get('/reports/databases')
    assert response.status_code == 403

    # Test view creation (should be denied)
    response = client.post('/reports/view/new', json={
        'title': 'New View',
        'database_id': test_report_view.database_id,
        'query': 'SELECT 1',
        'column_config': {}
    })
    assert response.status_code == 403

def test_soft_delete(test_user, test_db_connection, test_report_view):
    """Test soft delete functionality."""
    # Test database connection soft delete
    test_db_connection.deleted_at = datetime.utcnow()
    db.session.commit()
    
    connection = DatabaseConnection.query.filter_by(
        id=test_db_connection.id,
        deleted_at=None
    ).first()
    assert connection is None

    # Test report view soft delete
    test_report_view.deleted_at = datetime.utcnow()
    db.session.commit()
    
    view = ReportView.query.filter_by(
        id=test_report_view.id,
        deleted_at=None
    ).first()
    assert view is None
