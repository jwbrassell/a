"""Unit tests for the oncall plugin."""

import unittest
from datetime import datetime, timedelta, timezone
import zoneinfo
import json
import io
import csv
from flask import url_for
from app import create_app, db
from app.plugins.oncall import plugin
from app.plugins.oncall.models import Team, OnCallRotation
from app.models import User

class TestOnCallPlugin(unittest.TestCase):
    """Test cases for OnCall plugin."""
    
    def setUp(self):
        """Set up test environment."""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()
        
        # Create test user with required roles
        self.user = User(username='test_user', email='test@example.com')
        self.user.set_password('test_password')
        self.user.roles = ['admin', 'demo']  # Required roles for oncall plugin
        db.session.add(self.user)
        
        # Create test team
        self.team = Team(name='Test Team', color='primary')
        db.session.add(self.team)
        
        db.session.commit()
        
    def tearDown(self):
        """Clean up test environment."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        
    def login(self):
        """Helper method to log in test user."""
        return self.client.post('/login', data={
            'username': 'test_user',
            'password': 'test_password'
        }, follow_redirects=True)
        
    def test_plugin_initialization(self):
        """Test plugin initialization and configuration."""
        self.assertEqual(plugin.metadata.name, 'oncall')
        self.assertEqual(plugin.metadata.category, 'Operations')
        self.assertIn('admin', plugin.metadata.required_roles)
        self.assertEqual(plugin.metadata.icon, 'fa-calendar-alt')
        
    def test_team_model(self):
        """Test Team model operations."""
        # Test creation
        team = Team(name='New Team', color='success')
        db.session.add(team)
        db.session.commit()
        
        # Test retrieval
        saved_team = Team.query.filter_by(name='New Team').first()
        self.assertIsNotNone(saved_team)
        self.assertEqual(saved_team.color, 'success')
        
        # Test to_dict method
        team_dict = saved_team.to_dict()
        self.assertEqual(team_dict['name'], 'New Team')
        self.assertEqual(team_dict['color'], 'success')
        
    def test_rotation_model(self):
        """Test OnCallRotation model operations."""
        # Create test rotation
        central_tz = zoneinfo.ZoneInfo('America/Chicago')
        start_time = datetime.now(central_tz)
        end_time = start_time + timedelta(days=7)
        
        rotation = OnCallRotation(
            week_number=1,
            year=2024,
            person_name='Test Person',
            phone_number='123-456-7890',
            team_id=self.team.id,
            start_time=start_time.astimezone(timezone.utc),
            end_time=end_time.astimezone(timezone.utc)
        )
        db.session.add(rotation)
        db.session.commit()
        
        # Test retrieval
        saved_rotation = OnCallRotation.query.first()
        self.assertEqual(saved_rotation.person_name, 'Test Person')
        self.assertEqual(saved_rotation.team, self.team)
        
        # Test current on-call
        current = OnCallRotation.get_current_oncall()
        self.assertIsNotNone(current)
        self.assertEqual(current.person_name, 'Test Person')
        
    def test_index_route(self):
        """Test index route."""
        self.login()
        response = self.client.get(url_for('oncall.index'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Team', response.data)
        
    def test_team_api(self):
        """Test team management API."""
        self.login()
        
        # Test team creation
        response = self.client.post(url_for('oncall.manage_teams'),
            json={'name': 'API Team', 'color': 'danger'}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['name'], 'API Team')
        
        # Test team listing
        response = self.client.get(url_for('oncall.manage_teams'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(any(t['name'] == 'API Team' for t in data))
        
        # Test team update
        team_id = Team.query.filter_by(name='API Team').first().id
        response = self.client.put(url_for('oncall.manage_team', team_id=team_id),
            json={'name': 'Updated Team', 'color': 'warning'}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['name'], 'Updated Team')
        
        # Test team deletion
        response = self.client.delete(url_for('oncall.manage_team', team_id=team_id))
        self.assertEqual(response.status_code, 204)
        self.assertIsNone(Team.query.filter_by(name='Updated Team').first())
        
    def test_csv_upload(self):
        """Test CSV upload functionality."""
        self.login()
        
        # Create test CSV content
        csv_content = "week,name,phone\n1,John Doe,123-456-7890\n2,Jane Smith,098-765-4321"
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        
        # Test upload
        response = self.client.post(url_for('oncall.upload_oncall'),
            data={
                'file': (csv_file, 'test.csv'),
                'team': self.team.id,
                'year': '2024'
            },
            content_type='multipart/form-data'
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify rotations were created
        rotations = OnCallRotation.query.filter_by(team_id=self.team.id).all()
        self.assertEqual(len(rotations), 2)
        self.assertEqual(rotations[0].person_name, 'John Doe')
        self.assertEqual(rotations[1].person_name, 'Jane Smith')
        
    def test_calendar_events(self):
        """Test calendar events API."""
        self.login()
        
        # Create test rotation
        central_tz = zoneinfo.ZoneInfo('America/Chicago')
        start_time = datetime.now(central_tz)
        end_time = start_time + timedelta(days=7)
        
        rotation = OnCallRotation(
            week_number=1,
            year=2024,
            person_name='Calendar Test',
            phone_number='123-456-7890',
            team_id=self.team.id,
            start_time=start_time.astimezone(timezone.utc),
            end_time=end_time.astimezone(timezone.utc)
        )
        db.session.add(rotation)
        db.session.commit()
        
        # Test events API
        response = self.client.get(url_for('oncall.get_events', 
            start=(start_time - timedelta(days=1)).isoformat(),
            end=(end_time + timedelta(days=1)).isoformat()
        ))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['title'], 'Calendar Test')
        
    def test_current_oncall(self):
        """Test current on-call API."""
        self.login()
        
        # Create current rotation
        central_tz = zoneinfo.ZoneInfo('America/Chicago')
        start_time = datetime.now(central_tz) - timedelta(days=1)
        end_time = start_time + timedelta(days=7)
        
        rotation = OnCallRotation(
            week_number=1,
            year=2024,
            person_name='Current Test',
            phone_number='123-456-7890',
            team_id=self.team.id,
            start_time=start_time.astimezone(timezone.utc),
            end_time=end_time.astimezone(timezone.utc)
        )
        db.session.add(rotation)
        db.session.commit()
        
        # Test current API
        response = self.client.get(url_for('oncall.get_current_oncall'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['name'], 'Current Test')
        self.assertEqual(data['team'], 'Test Team')
        
    def test_timezone_handling(self):
        """Test timezone handling in rotations."""
        # Create rotation with specific timezone
        central_tz = zoneinfo.ZoneInfo('America/Chicago')
        start_time = datetime(2024, 1, 5, 17, 0, tzinfo=central_tz)  # Friday 5 PM Central
        end_time = start_time + timedelta(days=7)
        
        rotation = OnCallRotation(
            week_number=1,
            year=2024,
            person_name='TZ Test',
            phone_number='123-456-7890',
            team_id=self.team.id,
            start_time=start_time.astimezone(timezone.utc),
            end_time=end_time.astimezone(timezone.utc)
        )
        db.session.add(rotation)
        db.session.commit()
        
        # Verify timezone conversion
        saved_rotation = OnCallRotation.query.first()
        start_central = saved_rotation.start_time.replace(tzinfo=timezone.utc).astimezone(central_tz)
        
        self.assertEqual(start_central.hour, 17)  # Should be 5 PM
        self.assertEqual(start_central.minute, 0)
        self.assertEqual(start_central.tzname(), 'CST')  # Central Time
        
    def test_error_handling(self):
        """Test error handling in routes."""
        self.login()
        
        # Test invalid team creation
        response = self.client.post(url_for('oncall.manage_teams'),
            json={'color': 'danger'}  # Missing required name
        )
        self.assertEqual(response.status_code, 400)
        
        # Test invalid CSV upload
        csv_content = "invalid,csv,format\n1,2,3"
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        
        response = self.client.post(url_for('oncall.upload_oncall'),
            data={
                'file': (csv_file, 'test.csv'),
                'team': self.team.id,
                'year': '2024'
            },
            content_type='multipart/form-data'
        )
        self.assertEqual(response.status_code, 400)
        
        # Test invalid calendar date range
        response = self.client.get(url_for('oncall.get_events'))  # Missing required dates
        self.assertEqual(response.status_code, 400)
