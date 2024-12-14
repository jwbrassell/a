import os
import sys
import unittest
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from vault_utility import VaultUtility, VaultError, CSRFProtection, PluginCredentialManager

class TestVaultUtility(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.env_patcher = patch.dict('os.environ', {
            'VAULT_ADDR': 'https://127.0.0.1:8200',
            'VAULT_TOKEN': 'test-token'
        })
        self.env_patcher.start()
        
    def tearDown(self):
        """Clean up test environment."""
        self.env_patcher.stop()
        
    @patch('hvac.Client')
    def test_vault_initialization(self, mock_client):
        """Test Vault client initialization."""
        mock_client.return_value.is_authenticated.return_value = True
        mock_client.return_value.sys.list_mounted_secrets_engines.return_value = {
            'kv/': {'type': 'kv', 'options': {'version': '2'}}
        }
        
        vault = VaultUtility()
        self.assertIsNotNone(vault.client)
        self.assertEqual(vault.kv_v2_mount_point, 'kv')
        
    @patch('hvac.Client')
    def test_vault_https_enforcement(self, mock_client):
        """Test HTTPS enforcement."""
        with patch.dict('os.environ', {'VAULT_ADDR': 'http://127.0.0.1:8200'}):
            with patch('os.getenv') as mock_getenv:
                mock_getenv.return_value = 'production'
                with self.assertRaises(VaultError):
                    VaultUtility()
                    
    @patch('hvac.Client')
    def test_vault_localhost_restriction(self, mock_client):
        """Test localhost restriction."""
        with patch.dict('os.environ', {'VAULT_ADDR': 'https://example.com:8200'}):
            with self.assertRaises(VaultError):
                VaultUtility()
                
    @patch('hvac.Client')
    def test_development_mode_settings(self, mock_client):
        """Test development mode specific settings."""
        mock_client.return_value.is_authenticated.return_value = True
        mock_client.return_value.sys.list_mounted_secrets_engines.return_value = {
            'kv/': {'type': 'kv', 'options': {'version': '2'}}
        }
        
        with patch.dict('os.environ', {'FLASK_ENV': 'development'}):
            vault = VaultUtility()
            self.assertFalse(vault.client.session.verify)  # SSL verification disabled in dev
            
    @patch('hvac.Client')
    def test_production_mode_settings(self, mock_client):
        """Test production mode specific settings."""
        mock_client.return_value.is_authenticated.return_value = True
        mock_client.return_value.sys.list_mounted_secrets_engines.return_value = {
            'kv/': {'type': 'kv', 'options': {'version': '2'}}
        }
        
        with patch.dict('os.environ', {'FLASK_ENV': 'production'}):
            vault = VaultUtility()
            self.assertTrue(vault.client.session.verify)  # SSL verification enabled in prod

class TestCSRFProtection(unittest.TestCase):
    @patch('hvac.Client')
    def setUp(self, mock_client):
        """Set up test environment."""
        mock_client.return_value.is_authenticated.return_value = True
        mock_client.return_value.sys.list_mounted_secrets_engines.return_value = {
            'kv/': {'type': 'kv', 'options': {'version': '2'}}
        }
        
        self.vault = VaultUtility()
        self.csrf = self.vault.csrf
        
    def test_token_generation(self):
        """Test CSRF token generation."""
        token = self.csrf.generate_token()
        self.assertIsNotNone(token)
        self.assertIsInstance(token, str)
        self.assertTrue(len(token) > 32)  # Ensure sufficient token length
        
    def test_token_validation(self):
        """Test CSRF token validation."""
        token = self.csrf.generate_token()
        self.assertTrue(self.csrf.validate_token(token))
        self.assertFalse(self.csrf.validate_token('invalid-token'))
        
    def test_token_expiration(self):
        """Test token expiration."""
        with patch('datetime.datetime') as mock_datetime:
            # Set current time
            current_time = datetime.now()
            mock_datetime.utcnow.return_value = current_time
            
            # Generate token
            token = self.csrf.generate_token()
            
            # Test valid token (within 24 hours)
            mock_datetime.utcnow.return_value = current_time + timedelta(hours=23)
            self.assertTrue(self.csrf.validate_token(token))
            
            # Test expired token (after 24 hours)
            mock_datetime.utcnow.return_value = current_time + timedelta(hours=25)
            self.assertFalse(self.csrf.validate_token(token))
            
    def test_token_deletion(self):
        """Test token deletion."""
        token = self.csrf.generate_token()
        self.assertTrue(self.csrf.validate_token(token))
        
        self.csrf.delete_token(token)
        self.assertFalse(self.csrf.validate_token(token))

class TestPluginCredentialManager(unittest.TestCase):
    @patch('hvac.Client')
    def setUp(self, mock_client):
        """Set up test environment."""
        mock_client.return_value.is_authenticated.return_value = True
        mock_client.return_value.sys.list_mounted_secrets_engines.return_value = {
            'kv/': {'type': 'kv', 'options': {'version': '2'}}
        }
        
        self.vault = VaultUtility()
        self.plugin_creds = self.vault.plugin_credentials
        
    def test_store_credentials(self):
        """Test storing plugin credentials."""
        test_creds = {
            'api_key': 'test-key',
            'secret': 'test-secret'
        }
        
        self.plugin_creds.store_plugin_credentials('test-plugin', test_creds)
        retrieved_creds = self.plugin_creds.get_plugin_credentials('test-plugin')
        self.assertEqual(retrieved_creds, test_creds)
        
    def test_credential_rotation(self):
        """Test credential rotation functionality."""
        # Initial credentials
        initial_creds = {
            'api_key': 'initial-key',
            'secret': 'initial-secret'
        }
        
        # Store initial credentials
        self.plugin_creds.store_plugin_credentials('test-plugin', initial_creds)
        
        # New credentials for rotation
        new_creds = {
            'api_key': 'new-key',
            'secret': 'new-secret'
        }
        
        # Rotate credentials
        self.plugin_creds.rotate_plugin_credentials('test-plugin', new_creds)
        
        # Verify current credentials
        current_creds = self.plugin_creds.get_plugin_credentials('test-plugin')
        self.assertEqual(current_creds, new_creds)
        
        # Verify historical credentials
        history = self.plugin_creds.get_plugin_credentials('test-plugin/history')
        self.assertEqual(history['previous'], initial_creds)
        
    def test_nonexistent_credentials(self):
        """Test handling of nonexistent credentials."""
        result = self.plugin_creds.get_plugin_credentials('nonexistent-plugin')
        self.assertIsNone(result)
        
    def test_invalid_credentials(self):
        """Test handling of invalid credentials format."""
        with self.assertRaises(VaultError):
            self.plugin_creds.store_plugin_credentials('test-plugin', 'invalid-format')

class TestSecretManagement(unittest.TestCase):
    @patch('hvac.Client')
    def setUp(self, mock_client):
        """Set up test environment."""
        mock_client.return_value.is_authenticated.return_value = True
        mock_client.return_value.sys.list_mounted_secrets_engines.return_value = {
            'kv/': {'type': 'kv', 'options': {'version': '2'}}
        }
        
        self.vault = VaultUtility()
        
    def test_secret_lifecycle(self):
        """Test complete secret lifecycle."""
        # Create secret
        test_secret = {'key': 'value'}
        self.vault.store_secret('test/secret', test_secret)
        
        # Read secret
        retrieved = self.vault.get_secret('test/secret')
        self.assertEqual(retrieved, test_secret)
        
        # Update secret
        updated_secret = {'key': 'new-value'}
        self.vault.store_secret('test/secret', updated_secret)
        
        # Verify update
        retrieved = self.vault.get_secret('test/secret')
        self.assertEqual(retrieved, updated_secret)
        
        # Delete secret
        self.vault.delete_secret('test/secret')
        
        # Verify deletion
        retrieved = self.vault.get_secret('test/secret')
        self.assertIsNone(retrieved)
        
    def test_list_secrets(self):
        """Test listing secrets."""
        # Store some secrets
        self.vault.store_secret('test/secret1', {'key': 'value1'})
        self.vault.store_secret('test/secret2', {'key': 'value2'})
        
        # List secrets
        secrets = self.vault.list_secrets('test')
        self.assertIn('secret1', secrets)
        self.assertIn('secret2', secrets)

if __name__ == '__main__':
    unittest.main()
