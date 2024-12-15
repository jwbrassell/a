"""Unit tests for the handoffs plugin."""

import unittest
from datetime import datetime, timedelta
from flask import url_for
from app import create_app, db
from app.plugins.handoffs import plugin
from app.plugins.handoffs.models import Handoff, HandoffShift
from app.plugins.handoffs.forms import HandoffForm
from app.models import User

class TestHandoffsPlugin(unittest.TestCase):
    """Test cases for Handoffs plugin."""
    
    def setUp(self):
        """Set up test environment."""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()
        
        # Create test user
        self.user = User(username='test_user', email='test@example.com')
        self.user.set_password('test_password')
        db.session.add(self.user)
        
        # Create test shifts
        shifts = ['1st', '2nd', '3rd']
        for shift_name in shifts:
            shift = HandoffShift(name=shift_name)
            db.session.add(shift)
            
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
        self.assertEqual(plugin.metadata.name, 'handoffs')
        self.assertEqual(plugin.metadata.category, 'Operations')
        self.assertIn('user', plugin.metadata.required_roles)
        self.assertEqual(plugin.metadata.icon, 'fa-exchange-alt')
        
    def test_handoff_model(self):
        """Test Handoff model operations."""
        # Create test handoff
        handoff = Handoff(
            reporter_id=self.user.id,
            assigned_to='1st',
            priority='high',
            description='Test handoff',
            status='open'
        )
        db.session.add(handoff)
        db.session.commit()
        
        # Test retrieval
        saved_handoff = Handoff.query.get(handoff.id)
        self.assertEqual(saved_handoff.description, 'Test handoff')
        self.assertEqual(saved_handoff.status, 'open')
        self.assertEqual(saved_handoff.reporter_user, self.user)
        
        # Test to_dict method
        handoff_dict = saved_handoff.to_dict()
        self.assertEqual(handoff_dict['priority'], 'high')
        self.assertEqual(handoff_dict['assigned_to'], '1st')
        
    def test_handoff_form_validation(self):
        """Test HandoffForm validation."""
        form = HandoffForm()
        
        # Test required fields
        self.assertFalse(form.validate())
        self.assertIn('This field is required.', form.assigned_to.errors)
        self.assertIn('This field is required.', form.priority.errors)
        self.assertIn('This field is required.', form.description.errors)
        
        # Test valid data
        form = HandoffForm(data={
            'assigned_to': '1st',
            'priority': 'high',
            'description': 'Test handoff',
            'ticket': 'TICKET-123',
            'hostname': 'test-host',
            'kirke': 'KIRKE-456'
        })
        self.assertTrue(form.validate())
        
        # Test field length validation
        form = HandoffForm(data={
            'assigned_to': '1st',
            'priority': 'high',
            'description': 'x' * 301,  # Exceeds max length
            'ticket': 'x' * 101  # Exceeds max length
        })
        self.assertFalse(form.validate())
        self.assertIn('Field cannot be longer than 300 characters.', 
                     form.description.errors)
        self.assertIn('Field cannot be longer than 100 characters.',
                     form.ticket.errors)
        
        # Test bridge link validation
        form = HandoffForm(data={
            'assigned_to': '1st',
            'priority': 'high',
            'description': 'Test handoff',
            'has_bridge': True,
            'bridge_link': 'not-a-url'
        })
        self.assertFalse(form.validate())
        self.assertIn('Please enter a valid URL', form.bridge_link.errors)
        
    def test_index_route(self):
        """Test index route."""
        self.login()
        
        # Create test handoffs
        open_handoff = Handoff(
            reporter_id=self.user.id,
            assigned_to='1st',
            priority='high',
            description='Open handoff',
            status='open'
        )
        closed_handoff = Handoff(
            reporter_id=self.user.id,
            assigned_to='2nd',
            priority='medium',
            description='Closed handoff',
            status='closed',
            closed_at=datetime.utcnow()
        )
        db.session.add_all([open_handoff, closed_handoff])
        db.session.commit()
        
        # Test route
        response = self.client.get(url_for('handoffs.index'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Open handoff', response.data)
        self.assertIn(b'Closed handoff', response.data)
        
    def test_metrics_route(self):
        """Test metrics route."""
        self.login()
        
        # Create test data
        now = datetime.utcnow()
        handoffs = [
            # Today's handoffs
            Handoff(
                reporter_id=self.user.id,
                assigned_to='1st',
                priority='high',
                description='Today high',
                status='open',
                created_at=now
            ),
            Handoff(
                reporter_id=self.user.id,
                assigned_to='2nd',
                priority='medium',
                description='Today closed',
                status='closed',
                created_at=now - timedelta(hours=2),
                closed_at=now
            ),
            # Week old handoffs
            Handoff(
                reporter_id=self.user.id,
                assigned_to='3rd',
                priority='low',
                description='Week old',
                status='closed',
                created_at=now - timedelta(days=7),
                closed_at=now - timedelta(days=6)
            )
        ]
        db.session.add_all(handoffs)
        db.session.commit()
        
        # Test route
        response = self.client.get(url_for('handoffs.metrics'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Handoff Metrics', response.data)
        
    def test_create_route(self):
        """Test create route."""
        self.login()
        
        # Test GET request
        response = self.client.get(url_for('handoffs.create'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Create Handoff', response.data)
        
        # Test POST request with valid data
        data = {
            'assigned_to': '1st',
            'priority': 'high',
            'description': 'Test handoff',
            'ticket': 'TICKET-123',
            'hostname': 'test-host',
            'kirke': 'KIRKE-456',
            'has_bridge': False
        }
        response = self.client.post(url_for('handoffs.create'), 
                                  data=data, 
                                  follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Handoff created successfully', response.data)
        
        # Verify handoff was created
        handoff = Handoff.query.filter_by(description='Test handoff').first()
        self.assertIsNotNone(handoff)
        self.assertEqual(handoff.ticket, 'TICKET-123')
        
    def test_close_handoff_route(self):
        """Test close_handoff route."""
        self.login()
        
        # Create test handoff
        handoff = Handoff(
            reporter_id=self.user.id,
            assigned_to='1st',
            priority='high',
            description='Test handoff',
            status='open'
        )
        db.session.add(handoff)
        db.session.commit()
        
        # Test closing handoff
        response = self.client.post(
            url_for('handoffs.close_handoff', id=handoff.id),
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'success')
        
        # Verify handoff was closed
        handoff = Handoff.query.get(handoff.id)
        self.assertEqual(handoff.status, 'closed')
        self.assertIsNotNone(handoff.closed_at)
        
        # Test closing already closed handoff
        response = self.client.post(
            url_for('handoffs.close_handoff', id=handoff.id),
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data['status'], 'error')
