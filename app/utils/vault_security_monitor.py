import os
import logging
from datetime import datetime
from pathlib import Path
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from vault_utility import VaultUtility, VaultError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VaultSecurityMonitor:
    """Monitor and verify Vault security settings."""
    
    def __init__(self, vault_utility=None):
        """Initialize with optional VaultUtility instance."""
        self.vault = vault_utility or VaultUtility()
        self.is_development = os.getenv('FLASK_ENV') == 'development'
        
    def check_vault_security(self):
        """Perform comprehensive security check."""
        try:
            results = {
                'https_enabled': False,
                'localhost_only': False,
                'certificates_valid': False,
                'csrf_working': False,
                'security_headers': False,
                'cert_expiry_days': None,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Check HTTPS
            results['https_enabled'] = self.vault.vault_url.startswith('https://')
            if not results['https_enabled'] and not self.is_development:
                logger.error('HTTPS is not enabled')
            
            # Check localhost restriction
            parsed_url = self.vault.vault_url.split('://')[-1].split(':')[0]
            results['localhost_only'] = parsed_url in ['localhost', '127.0.0.1']
            if not results['localhost_only']:
                logger.error('Vault is not restricted to localhost')
            
            # Check certificates if not in development
            if not self.is_development:
                try:
                    self.vault._verify_certificates()
                    results['certificates_valid'] = True
                    
                    # Check certificate expiry
                    days_until_expiry = self.check_certificate_expiry()
                    results['cert_expiry_days'] = days_until_expiry
                    
                    if days_until_expiry < 30:
                        logger.warning(f'Certificate will expire in {days_until_expiry} days')
                except Exception as e:
                    if not self.is_development:
                        logger.error(f'Certificate verification failed: {e}')
            else:
                # In development, mark as valid
                results['certificates_valid'] = True
                results['cert_expiry_days'] = 365  # Placeholder value
            
            # Test CSRF
            try:
                token = self.vault.csrf.generate_token()
                results['csrf_working'] = self.vault.csrf.validate_token(token)
                if not results['csrf_working']:
                    logger.error('CSRF token validation failed')
            except Exception as e:
                logger.error(f'CSRF check failed: {e}')
            
            return results
            
        except Exception as e:
            logger.error(f'Security check failed: {e}')
            raise VaultError(f'Security check failed: {str(e)}')

    def check_certificate_expiry(self):
        """Check certificate expiration and return days until expiry."""
        if self.is_development:
            return 365  # Return placeholder value in development
            
        try:
            cert_path = os.getenv('VAULT_CLIENT_CERT')
            if not cert_path:
                raise VaultError('Client certificate path not set')
                
            with open(cert_path, 'rb') as f:
                cert_data = f.read()
                cert = x509.load_pem_x509_certificate(cert_data, default_backend())
                
            expiry_date = cert.not_valid_after
            days_until_expiry = (expiry_date - datetime.utcnow()).days
            
            return days_until_expiry
            
        except Exception as e:
            logger.error(f'Failed to check certificate expiry: {e}')
            raise VaultError(f'Certificate expiry check failed: {str(e)}')

    def monitor_file_permissions(self):
        """Monitor sensitive file permissions."""
        if self.is_development:
            return {
                'permissions_valid': True,
                'issues': [],
                'timestamp': datetime.utcnow().isoformat()
            }
            
        sensitive_files = {
            'CA Certificate': os.getenv('VAULT_CACERT'),
            'Client Certificate': os.getenv('VAULT_CLIENT_CERT'),
            'Client Key': os.getenv('VAULT_CLIENT_KEY')
        }
        
        results = {
            'permissions_valid': True,
            'issues': [],
            'timestamp': datetime.utcnow().isoformat()
        }
        
        for name, path in sensitive_files.items():
            if not path:
                results['issues'].append(f'{name} path not set')
                results['permissions_valid'] = False
                continue
                
            try:
                stat = os.stat(path)
                if stat.st_mode & 0o777 != 0o600:
                    results['issues'].append(
                        f'{name} has incorrect permissions: {oct(stat.st_mode & 0o777)}'
                    )
                    results['permissions_valid'] = False
            except Exception as e:
                results['issues'].append(f'Error checking {name}: {str(e)}')
                results['permissions_valid'] = False
        
        return results

    def check_security_headers(self, response):
        """Verify security headers in response."""
        required_headers = {
            'Content-Security-Policy': None,  # Complex validation
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': None,  # Contains dynamic max-age
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
        
        results = {
            'headers_valid': True,
            'missing_headers': [],
            'invalid_headers': [],
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Skip detailed header checks in development
        if self.is_development:
            return results
            
        for header, expected_value in required_headers.items():
            if header not in response.headers:
                results['headers_valid'] = False
                results['missing_headers'].append(header)
            elif expected_value and response.headers[header] != expected_value:
                results['headers_valid'] = False
                results['invalid_headers'].append({
                    'header': header,
                    'expected': expected_value,
                    'actual': response.headers[header]
                })
        
        # Special check for CSP
        if 'Content-Security-Policy' in response.headers:
            csp = response.headers['Content-Security-Policy']
            if not all(directive in csp for directive in [
                "default-src 'self'",
                "script-src",
                "style-src",
                "img-src",
                "font-src",
                "frame-ancestors 'none'",
                "form-action 'self'"
            ]):
                results['headers_valid'] = False
                results['invalid_headers'].append({
                    'header': 'Content-Security-Policy',
                    'issue': 'Missing required directives'
                })
        
        return results

    def generate_security_report(self):
        """Generate comprehensive security report."""
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'vault_security': None,
            'file_permissions': None,
            'certificate_status': None,
            'overall_status': 'healthy'  # Default to healthy in development
        }
        
        try:
            # Run security checks
            report['vault_security'] = self.check_vault_security()
            report['file_permissions'] = self.monitor_file_permissions()
            
            # Add certificate information
            days_until_expiry = self.check_certificate_expiry()
            report['certificate_status'] = {
                'days_until_expiry': days_until_expiry,
                'status': 'valid' if days_until_expiry > 0 else 'expired',
                'warning_level': 'critical' if days_until_expiry < 7 else 
                               'warning' if days_until_expiry < 30 else 'ok'
            }
            
            # Add overall status
            if not self.is_development:
                if (not report['vault_security']['https_enabled'] or
                    not report['vault_security']['localhost_only'] or
                    not report['vault_security']['certificates_valid'] or
                    not report['vault_security']['csrf_working'] or
                    not report['file_permissions']['permissions_valid'] or
                    days_until_expiry < 0):
                    report['overall_status'] = 'critical'
                elif (days_until_expiry < 30 or 
                      len(report['file_permissions']['issues']) > 0):
                    report['overall_status'] = 'warning'
            
        except Exception as e:
            logger.error(f'Failed to generate security report: {e}')
            if not self.is_development:
                report['overall_status'] = 'error'
                report['error'] = str(e)
        
        return report

def main():
    """Run security monitoring as a standalone script."""
    try:
        monitor = VaultSecurityMonitor()
        report = monitor.generate_security_report()
        
        # Print report
        print("\nVault Security Report")
        print("=" * 50)
        print(f"Timestamp: {report['timestamp']}")
        print(f"Overall Status: {report['overall_status'].upper()}")
        print("\nSecurity Checks:")
        for key, value in report['vault_security'].items():
            print(f"  {key}: {value}")
        print("\nFile Permissions:")
        print(f"  Valid: {report['file_permissions']['permissions_valid']}")
        if report['file_permissions']['issues']:
            print("  Issues:")
            for issue in report['file_permissions']['issues']:
                print(f"    - {issue}")
        print("\nCertificate Status:")
        print(f"  Days until expiry: {report['certificate_status']['days_until_expiry']}")
        print(f"  Status: {report['certificate_status']['status']}")
        print(f"  Warning Level: {report['certificate_status']['warning_level']}")
        
    except Exception as e:
        logger.error(f"Failed to run security monitoring: {e}")
        raise

if __name__ == '__main__':
    main()
