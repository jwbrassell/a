import os
import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock
import warnings
from flask import Response

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from utils.vault_security_monitor import VaultSecurityMonitor
from vault_utility import VaultUtility, VaultError

class TestVaultSecurityMonitor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        warnings.filterwarnings(
            "ignore",
            category=DeprecationWarning
        )
        
        # Set up test environment variables
        cls.env_vars = {
            'VAULT_ADDR': 'https://127.0.0.1:8200',
            'VAULT_TOKEN': 'test-token',
            'VAULT_CACERT': '/path/to/ca.crt',
            'VAULT_CLIENT_CERT': '/path/to/client.crt',
            'VAULT_CLIENT_KEY': '/path/to/client.key'
        }

    def setUp(self):
        """Set up test cases."""
        self.env_patcher = patch.dict('os.environ', self.env_vars)
        self.env_patcher.start()
        
        # Mock VaultUtility
        self.mock_vault = MagicMock(spec=VaultUtility)
        self.mock_vault.vault_url = 'https://127.0.0.1:8200'
        self.mock_vault.csrf = MagicMock()
        
        # Create monitor instance with mock vault
        self.monitor = VaultSecurityMonitor(self.mock_vault)

    def tearDown(self):
        """Clean up after each test."""
        self.env_patcher.stop()

    def test_check_vault_security(self):
        """Test comprehensive security check."""
        # Mock certificate expiry check
        with patch.object(self.monitor, 'check_certificate_expiry') as mock_expiry:
            mock_expiry.return_value = 90  # 90 days until expiry
            
            # Mock CSRF token validation
            self.mock_vault.csrf.generate_token.return_value = 'test-token'
            self.mock_vault.csrf.validate_token.return_value = True
            
            results = self.monitor.check_vault_security()
            
            # Verify results
            self.assertTrue(results['https_enabled'])
            self.assertTrue(results['localhost_only'])
            self.assertTrue(results['csrf_working'])
            self.assertEqual(results['cert_expiry_days'], 90)

    @patch('builtins.open', create=True)
    @patch('cryptography.x509.load_pem_x509_certificate')
    def test_check_certificate_expiry(self, mock_load_cert, mock_open):
        """Test certificate expiry check."""
        # Mock certificate
        mock_cert = MagicMock()
        mock_cert.not_valid_after = datetime.utcnow() + timedelta(days=90)
        mock_load_cert.return_value = mock_cert
        
        # Mock file operations
        mock_open.return_value.__enter__.return_value.read.return_value = b'mock cert data'
        
        days = self.monitor.check_certificate_expiry()
        self.assertEqual(days, 90)

    @patch('os.stat')
    def test_monitor_file_permissions(self, mock_stat):
        """Test file permissions monitoring."""
        # Mock stat result with correct permissions (0600)
        mock_stat_result = MagicMock()
        mock_stat_result.st_mode = 0o600
        mock_stat.return_value = mock_stat_result
        
        results = self.monitor.monitor_file_permissions()
        
        self.assertTrue(results['permissions_valid'])
        self.assertEqual(len(results['issues']), 0)
        
        # Test with incorrect permissions
        mock_stat_result.st_mode = 0o644
        results = self.monitor.monitor_file_permissions()
        
        self.assertFalse(results['permissions_valid'])
        self.assertTrue(len(results['issues']) > 0)

    def test_check_security_headers(self):
        """Test security headers verification."""
        # Create response with correct headers
        response = Response('Test')
        response.headers.update({
            'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; frame-ancestors 'none'; form-action 'self'",
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        })
        
        results = self.monitor.check_security_headers(response)
        
        self.assertTrue(results['headers_valid'])
        self.assertEqual(len(results['missing_headers']), 0)
        self.assertEqual(len(results['invalid_headers']), 0)
        
        # Test with missing header
        response.headers.pop('X-Frame-Options')
        results = self.monitor.check_security_headers(response)
        
        self.assertFalse(results['headers_valid'])
        self.assertTrue('X-Frame-Options' in results['missing_headers'])

    def test_generate_security_report(self):
        """Test security report generation."""
        # Mock all the component checks
        with patch.object(self.monitor, 'check_vault_security') as mock_security, \
             patch.object(self.monitor, 'monitor_file_permissions') as mock_permissions, \
             patch.object(self.monitor, 'check_certificate_expiry') as mock_expiry:
            
            # Set up mock returns
            mock_security.return_value = {
                'https_enabled': True,
                'localhost_only': True,
                'certificates_valid': True,
                'csrf_working': True,
                'cert_expiry_days': 90,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            mock_permissions.return_value = {
                'permissions_valid': True,
                'issues': [],
                'timestamp': datetime.utcnow().isoformat()
            }
            
            mock_expiry.return_value = 90
            
            report = self.monitor.generate_security_report()
            
            # Verify report structure and content
            self.assertIn('timestamp', report)
            self.assertIn('overall_status', report)
            self.assertIn('vault_security', report)
            self.assertIn('file_permissions', report)
            self.assertIn('certificate_status', report)
            
            # Verify overall status is healthy
            self.assertEqual(report['overall_status'], 'healthy')
            
            # Test with warning conditions
            mock_expiry.return_value = 20  # 20 days until expiry
            report = self.monitor.generate_security_report()
            self.assertEqual(report['overall_status'], 'warning')
            
            # Test with critical conditions
            mock_security.return_value['https_enabled'] = False
            report = self.monitor.generate_security_report()
            self.assertEqual(report['overall_status'], 'critical')

if __name__ == '__main__':
    unittest.main()
