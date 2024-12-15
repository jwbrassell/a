"""Test suite for request tracking functionality."""

import pytest
from datetime import datetime
from flask import url_for
from app import db
from app.models import UserActivity, PageVisit

def test_request_tracking_anonymous(client):
    """Test request tracking for anonymous users."""
    # Make a request
    response = client.get('/')
    assert response.status_code in [200, 302]  # May redirect to login

    # Check page visit was recorded
    visit = PageVisit.query.order_by(PageVisit.id.desc()).first()
    assert visit is not None
    assert visit.route == '/'
    assert visit.method == 'GET'
    assert visit.user_id is None
    assert visit.username is None
    assert visit.ip_address is not None

def test_request_tracking_authenticated(client, test_user):
    """Test request tracking for authenticated users."""
    # Login
    client.post('/login', data={'username': test_user.username, 'password': 'password'})

    # Make a request
    response = client.get('/profile')
    assert response.status_code in [200, 302]

    # Check user activity was recorded
    activity = UserActivity.query.order_by(UserActivity.id.desc()).first()
    assert activity is not None
    assert activity.user_id == test_user.id
    assert activity.username == test_user.username
    assert 'Accessed' in activity.activity
    assert activity.timestamp is not None

    # Check page visit was recorded
    visit = PageVisit.query.order_by(PageVisit.id.desc()).first()
    assert visit is not None
    assert visit.route == '/profile'
    assert visit.method == 'GET'
    assert visit.user_id == test_user.id
    assert visit.username == test_user.username
    assert visit.ip_address is not None
    assert visit.timestamp is not None

def test_static_file_tracking(client):
    """Test that static file requests are not tracked."""
    # Request a static file
    response = client.get('/static/test.css')
    assert response.status_code in [404, 304]  # File might not exist

    # Get latest page visit
    visit = PageVisit.query.order_by(PageVisit.id.desc()).first()
    
    # If there is a visit record, verify it's not for the static file
    if visit:
        assert not visit.route.startswith('/static/')

def test_request_tracking_error_handling(client, test_user, monkeypatch):
    """Test error handling in request tracking."""
    # Login
    client.post('/login', data={'username': test_user.username, 'password': 'password'})

    # Simulate database error by making session commit raise an exception
    def mock_commit():
        raise Exception("Database error")

    monkeypatch.setattr(db.session, 'commit', mock_commit)

    # Make a request - should not fail even if tracking fails
    response = client.get('/profile')
    assert response.status_code in [200, 302]

def test_request_tracking_performance(client, test_user, benchmark):
    """Test performance impact of request tracking."""
    # Login
    client.post('/login', data={'username': test_user.username, 'password': 'password'})

    def make_request():
        return client.get('/profile')

    # Benchmark the request
    result = benchmark(make_request)
    assert result.status_code in [200, 302]

def test_request_tracking_data_integrity(client, test_user):
    """Test data integrity of tracked information."""
    # Login
    client.post('/login', data={'username': test_user.username, 'password': 'password'})

    # Make requests with different methods
    endpoints = [
        ('GET', '/profile'),
        ('POST', '/profile'),
        ('GET', '/documents'),
    ]

    for method, endpoint in endpoints:
        if method == 'GET':
            response = client.get(endpoint)
        else:
            response = client.post(endpoint)
        assert response.status_code in [200, 302, 403]  # May be forbidden

        # Verify activity record
        activity = UserActivity.query.filter_by(
            user_id=test_user.id,
            username=test_user.username
        ).order_by(UserActivity.id.desc()).first()
        
        assert activity is not None
        assert isinstance(activity.timestamp, datetime)

        # Verify page visit record
        visit = PageVisit.query.filter_by(
            route=endpoint,
            method=method,
            user_id=test_user.id,
            username=test_user.username
        ).order_by(PageVisit.id.desc()).first()
        
        assert visit is not None
        assert isinstance(visit.timestamp, datetime)
        assert visit.status_code in [200, 302, 403]
