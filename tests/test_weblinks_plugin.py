"""Test suite for Weblinks plugin."""

import pytest
from datetime import datetime
from flask import url_for
from app import db
from app.plugins.weblinks.models import WebLink, WebLinkCategory, WebLinkTag

@pytest.fixture
def test_category(test_user):
    """Create a test category."""
    category = WebLinkCategory(
        name="Test Category",
        created_by=test_user.id,
        updated_by=test_user.id
    )
    db.session.add(category)
    db.session.commit()
    return category

@pytest.fixture
def test_tag(test_user):
    """Create a test tag."""
    tag = WebLinkTag(
        name="Test Tag",
        created_by=test_user.id,
        updated_by=test_user.id
    )
    db.session.add(tag)
    db.session.commit()
    return tag

@pytest.fixture
def test_link(test_user, test_category, test_tag):
    """Create a test web link."""
    link = WebLink(
        url="https://example.com",
        friendly_name="Test Link",
        notes="Test notes",
        icon="fa-test",
        category_id=test_category.id,
        created_by=test_user.id,
        updated_by=test_user.id
    )
    link.tags.append(test_tag)
    db.session.add(link)
    db.session.commit()
    return link

def test_plugin_initialization(app):
    """Test that the plugin initializes correctly."""
    assert 'weblinks' in app.blueprints
    assert '/weblinks' in [rule.rule for rule in app.url_map.iter_rules()]

def test_models(test_user):
    """Test model creation and relationships."""
    # Create category
    category = WebLinkCategory(
        name="Test Category",
        created_by=test_user.id,
        updated_by=test_user.id
    )
    db.session.add(category)
    
    # Create tag
    tag = WebLinkTag(
        name="Test Tag",
        created_by=test_user.id,
        updated_by=test_user.id
    )
    db.session.add(tag)
    
    # Create link
    link = WebLink(
        url="https://example.com",
        friendly_name="Test Link",
        notes="Test notes",
        icon="fa-test",
        category=category,
        created_by=test_user.id,
        updated_by=test_user.id
    )
    link.tags.append(tag)
    db.session.add(link)
    db.session.commit()

    # Test relationships
    assert link.category == category
    assert link.tags[0] == tag
    assert link.creator == test_user
    assert link.updater == test_user
    assert category.links[0] == link
    assert tag.links[0] == link

def test_link_routes(client, test_user, test_category, test_tag):
    """Test link management routes."""
    # Login
    client.post('/login', data={'username': test_user.username, 'password': 'password'})

    # Test link creation
    response = client.post('/weblinks/link/add', data={
        'url': 'https://example.com',
        'friendly_name': 'Test Link',
        'notes': 'Test notes',
        'icon': 'fa-test',
        'category': test_category.id,
        'tags': [test_tag.id]
    })
    assert response.status_code in [200, 302]

    # Test link listing
    response = client.get('/weblinks/api/links')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['data']) > 0

    # Test link search
    response = client.get('/weblinks/search?q=Test')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) > 0

def test_category_routes(client, test_user):
    """Test category management routes."""
    # Login
    client.post('/login', data={'username': test_user.username, 'password': 'password'})

    # Test category creation
    response = client.post('/weblinks/category/add', data={
        'name': 'New Category'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    category_id = data['id']

    # Test category listing
    response = client.get('/weblinks/api/categories')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) > 0

    # Test category deletion
    response = client.delete(f'/weblinks/category/{category_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True

def test_tag_routes(client, test_user):
    """Test tag management routes."""
    # Login
    client.post('/login', data={'username': test_user.username, 'password': 'password'})

    # Test tag creation
    response = client.post('/weblinks/tag/add', data={
        'name': 'New Tag'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    tag_id = data['id']

    # Test tag listing
    response = client.get('/weblinks/api/tags')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) > 0

    # Test tag deletion
    response = client.delete(f'/weblinks/tag/{tag_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True

def test_import_export(client, test_user, test_link):
    """Test import/export functionality."""
    # Login
    client.post('/login', data={'username': test_user.username, 'password': 'password'})

    # Test export
    response = client.get('/weblinks/export/csv')
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'text/csv'
    assert 'attachment' in response.headers['Content-Disposition']

    # Test import
    with open('test_import.csv', 'w') as f:
        f.write('URL,Friendly Name,Category,Tags,Notes,Icon\n')
        f.write('https://test.com,Test Import,Test Category,Test Tag,Test Notes,fa-test\n')

    with open('test_import.csv', 'rb') as f:
        response = client.post('/weblinks/import/csv', data={
            'file': (f, 'test_import.csv')
        })
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['imported'] > 0

def test_soft_delete(test_user, test_link):
    """Test soft delete functionality."""
    # Test link soft delete
    test_link.deleted_at = datetime.utcnow()
    test_link.updated_by = test_user.id
    db.session.commit()
    
    # Verify link is not returned in active queries
    link = WebLink.query.filter_by(
        id=test_link.id,
        deleted_at=None
    ).first()
    assert link is None

def test_permissions(client, test_user):
    """Test permission restrictions."""
    # Login as user without required roles
    client.post('/login', data={'username': test_user.username, 'password': 'password'})

    # Test protected routes
    protected_routes = [
        ('/weblinks/link/add', 'GET'),
        ('/weblinks/category/add', 'POST'),
        ('/weblinks/tag/add', 'POST'),
        ('/weblinks/export/csv', 'GET')
    ]

    for route, method in protected_routes:
        if method == 'GET':
            response = client.get(route)
        else:
            response = client.post(route)
        assert response.status_code in [302, 403]  # Either redirect to login or forbidden
