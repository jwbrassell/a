import os
import sys
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import warnings
import hvac
from datetime import datetime, timedelta
from flask import Response

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from vault_utility import VaultUtility, VaultError, SecurityHeaders

class TestVaultSecurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        # Suppress deprecation warnings
        warnings.filterwarnings(
            "ignore",
            category=DeprecationWarning
        )
        
        # Create temporary directory for test certificates
        cls.temp_dir = tempfile.mkdtemp()
        
        # Set up test environment variables
        cls.env_vars = {
            'VAULT_ADDR': 'https://127.0.0.1:8200',
            'VAULT_TOKEN': 'test-token',
            'VAULT_CACERT': os.path.join(cls.temp_dir, 'ca.crt'),
            'VAULT_CLIENT_CERT': os.path.join(cls.temp_dir, 'server.crt'),
            'VAULT_CLIENT_KEY': os.path.join(cls.temp_dir, 'server.key')
        }
        
        # Create mock certificate files
        for path in [cls.env_vars['VAULT_CACERT'], 
                    cls.env_vars['VAULT_CLIENT_CERT'], 
                    cls.env_vars['VAULT_CLIENT_KEY']]:
            with open(path, 'w') as f:
                f.write('mock certificate content')
            os.chmod(path, 0o600)

    def setUp(self):
        """Set up test cases."""
        self.mock_client = MagicMock(spec=hvac.Client)
        self.mock_client.is_authenticated.return_value = True
        
        # Mock KV v2 secrets engine
        self.mock_client.sys.list_mounted_secrets_engines.return_value = {
            'secret/': {
                'type': 'kv',
                'options': {'version': '2'}
            }
        }
        
        # Set up environment variables for each test
        self.env_patcher = patch.dict('os.environ', self.env_vars)
        self.env_patcher.start()

    def tearDown(self):
        """Clean up after each test."""
        self.env_patcher.stop()

    def test_https_enforcement_production(self):
        """Test HTTPS enforcement in production."""
        with patch.dict('os.environ', {'FLASK_ENV': 'production'}):
            # Test with HTTP URL
            with self.assertRaises(VaultError) as context:
                VaultUtility(vault_url='http://127.0.0.1:8200')
            self.assertIn('HTTPS is required', str(context.exception))
            
            # Test with HTTPS URL
            with patch('hvac.Client') as mock_hvac:
                mock_hvac.return_value = self.mock_client
                vault = VaultUtility(vault_url='https://127.0.0.1:8200')
                self.assertIsNotNone(vault)

    def test_localhost_restriction(self):
        """Test localhost restriction."""
        with patch('hvac.Client') as mock_hvac:
            mock_hvac.return_value = self.mock_client
            
            # Test non-localhost URL
            with self.assertRaises(VaultError) as context:
                VaultUtility(vault_url='https://example.com:8200')
            self.assertIn('localhost only', str(context.exception))
            
            # Test localhost URL
            vault = VaultUtility(vault_url='https://127.0.0.1:8200')
            self.assertIsNotNone(vault)

    def test_certificate_verification(self):
        """Test certificate verification in production."""
        with patch.dict('os.environ', {'FLASK_ENV': 'production'}):
            with patch('hvac.Client') as mock_hvac:
                mock_hvac.return_value = self.mock_client
                vault = VaultUtility()
                self.assertIsNotNone(vault)

    def test_security_headers(self):
        """Test security headers application."""
        # Create a real Flask Response object
        response = Response('Test response')
        secured_response = SecurityHeaders.apply_security_headers(response)
        
        # Verify all security headers are set
        self.assertIn('Content-Security-Policy', secured_response.headers)
        self.assertIn('X-Content-Type-Options', secured_response.headers)
        self.assertIn('X-Frame-Options', secured_response.headers)
        self.assertIn('X-XSS-Protection', secured_response.headers)
        self.assertIn('Strict-Transport-Security', secured_response.headers)
        self.assertIn('Referrer-Policy', secured_response.headers)
        
        # Verify header values
        self.assertEqual(secured_response.headers['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(secured_response.headers['X-Frame-Options'], 'DENY')
        self.assertEqual(secured_response.headers['X-XSS-Protection'], '1; mode=block')
        self.assertIn('max-age=31536000', secured_response.headers['Strict-Transport-Security'])
        self.assertEqual(secured_response.headers['Referrer-Policy'], 'strict-origin-when-cross-origin')

    def test_csrf_protection(self):
        """Test CSRF protection."""
        with patch('hvac.Client') as mock_hvac:
            mock_hvac.return_value = self.mock_client
            vault = VaultUtility(vault_url='https://127.0.0.1:8200')
            
            # Set up mock for token storage
            test_token = None
            test_data = None
            
            def mock_store_token(mount_point, path, secret):
                nonlocal test_token, test_data
                test_token = path.split('/')[-1]
                test_data = secret
                return {'data': {'version': 1}}
            
            def mock_read_token(mount_point, path):
                nonlocal test_token, test_data
                if path.split('/')[-1] == test_token:
                    return {'data': {'data': test_data}}
                raise hvac.exceptions.InvalidPath()
            
            # Set up the mocks
            self.mock_client.secrets.kv.v2.create_or_update_secret.side_effect = mock_store_token
            self.mock_client.secrets.kv.v2.read_secret_version.side_effect = mock_read_token
            
            # Test token generation
            token = vault.csrf.generate_token()
            self.assertIsNotNone(token)
            self.assertTrue(isinstance(token, str))
            
            # Test token validation
            self.assertTrue(vault.csrf.validate_token(token))
            
            # Test invalid token
            self.assertFalse(vault.csrf.validate_token('invalid-token'))
            
            # Test expired token
            def mock_read_expired_token(mount_point, path):
                return {
                    'data': {
                        'data': {
                            'expiry': (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                            'created': (datetime.utcnow() - timedelta(hours=25)).isoformat()
                        }
                    }
                }
            
            self.mock_client.secrets.kv.v2.read_secret_version.side_effect = mock_read_expired_token
            self.assertFalse(vault.csrf.validate_token(token))

    def test_plugin_credential_manager(self):
        """Test plugin credential management."""
        with patch('hvac.Client') as mock_hvac:
            mock_hvac.return_value = self.mock_client
            vault = VaultUtility(vault_url='https://127.0.0.1:8200')
            
            # Test storing credentials
            test_creds = {'username': 'test', 'password': 'secret'}
            vault.plugin_credentials.store_plugin_credentials('test_plugin', test_creds)
            
            # Verify store was called
            self.mock_client.secrets.kv.v2.create_or_update_secret.assert_called_once()
            
            # Test retrieving credentials
            self.mock_client.secrets.kv.v2.read_secret_version.return_value = {
                'data': {
                    'data': test_creds
                }
            }
            retrieved_creds = vault.plugin_credentials.get_plugin_credentials('test_plugin')
            self.assertEqual(retrieved_creds, test_creds)

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(cls.temp_dir)

if __name__ == '__main__':
    unittest.main()
