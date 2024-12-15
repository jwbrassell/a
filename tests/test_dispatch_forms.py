"""Unit tests for dispatch plugin forms."""

import unittest
from app.plugins.dispatch.forms import DispatchForm, TeamForm, PriorityForm

class TestDispatchForm(unittest.TestCase):
    """Test cases for DispatchForm."""
    
    def setUp(self):
        self.form = DispatchForm()
        
    def test_required_fields(self):
        """Test that required fields are enforced."""
        self.assertFalse(self.form.validate())
        self.assertIn('This field is required.', self.form.team.errors)
        self.assertIn('This field is required.', self.form.priority.errors)
        self.assertIn('This field is required.', self.form.description.errors)
        
    def test_description_length(self):
        """Test description length validation."""
        self.form.description.data = 'a' * 2001  # Exceeds max length
        self.assertFalse(self.form.validate())
        self.assertIn('Description must be between 1 and 2000 characters', 
                     self.form.description.errors)
                     
    def test_bridge_link_validation(self):
        """Test bridge link validation when bridge is enabled."""
        self.form.is_bridge.data = True
        self.form.bridge_link.data = ''
        self.assertFalse(self.form.validate())
        self.assertIn('Bridge link is required when bridge is enabled',
                     self.form.bridge_link.errors)
                     
        # Test invalid URL
        self.form.bridge_link.data = 'not-a-url'
        self.assertFalse(self.form.validate())
        self.assertIn('Please enter a valid URL',
                     self.form.bridge_link.errors)
                     
        # Test valid URL
        self.form.bridge_link.data = 'https://example.com'
        # Note: Other required fields would still cause validation to fail
        
    def test_rma_info_validation(self):
        """Test RMA info validation when RMA is enabled."""
        self.form.is_rma.data = True
        self.form.rma_info.data = ''
        self.assertFalse(self.form.validate())
        self.assertIn('RMA information is required when RMA is enabled',
                     self.form.rma_info.errors)
                     
        # Test length validation
        self.form.rma_info.data = 'a' * 1001  # Exceeds max length
        self.assertFalse(self.form.validate())
        self.assertIn('RMA information must not exceed 1000 characters',
                     self.form.rma_info.errors)

class TestTeamForm(unittest.TestCase):
    """Test cases for TeamForm."""
    
    def setUp(self):
        self.form = TeamForm()
        
    def test_required_fields(self):
        """Test that required fields are enforced."""
        self.assertFalse(self.form.validate())
        self.assertIn('This field is required.', self.form.name.errors)
        self.assertIn('This field is required.', self.form.email.errors)
        
    def test_name_length(self):
        """Test team name length validation."""
        self.form.name.data = 'a' * 65  # Exceeds max length
        self.assertFalse(self.form.validate())
        self.assertIn('Team name must be between 1 and 64 characters',
                     self.form.name.errors)
                     
    def test_email_validation(self):
        """Test email format validation."""
        self.form.email.data = 'not-an-email'
        self.assertFalse(self.form.validate())
        self.assertIn('Please enter a valid email address',
                     self.form.email.errors)
                     
        # Test valid email
        self.form.email.data = 'team@example.com'
        # Note: Other required fields would still cause validation to fail
        
    def test_description_length(self):
        """Test description length validation."""
        self.form.description.data = 'a' * 257  # Exceeds max length
        self.assertFalse(self.form.validate())
        self.assertIn('Description must not exceed 256 characters',
                     self.form.description.errors)

class TestPriorityForm(unittest.TestCase):
    """Test cases for PriorityForm."""
    
    def setUp(self):
        self.form = PriorityForm()
        
    def test_required_fields(self):
        """Test that required fields are enforced."""
        self.assertFalse(self.form.validate())
        self.assertIn('This field is required.', self.form.name.errors)
        self.assertIn('This field is required.', self.form.color.errors)
        self.assertIn('This field is required.', self.form.icon.errors)
        
    def test_name_length(self):
        """Test priority name length validation."""
        self.form.name.data = 'a' * 33  # Exceeds max length
        self.assertFalse(self.form.validate())
        self.assertIn('Priority name must be between 1 and 32 characters',
                     self.form.name.errors)
                     
    def test_color_validation(self):
        """Test color hex code validation."""
        # Test missing #
        self.form.color.data = '000000'
        self.assertFalse(self.form.validate())
        self.assertIn('Color must start with #',
                     self.form.color.errors)
                     
        # Test invalid hex
        self.form.color.data = '#GGGGGG'
        self.assertFalse(self.form.validate())
        self.assertIn('Color must be a valid hex code (e.g. #FF0000)',
                     self.form.color.errors)
                     
        # Test valid hex
        self.form.color.data = '#FF0000'
        # Note: Other required fields would still cause validation to fail
        
    def test_icon_length(self):
        """Test icon class length validation."""
        self.form.icon.data = 'a' * 33  # Exceeds max length
        self.assertFalse(self.form.validate())
        self.assertIn('Icon class must be between 1 and 32 characters',
                     self.form.icon.errors)
