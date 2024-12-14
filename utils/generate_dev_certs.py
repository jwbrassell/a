#!/usr/bin/env python3
"""
Development SSL Certificate Generator
Generates self-signed certificates for local development HTTPS
"""

import os
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CertificateGenerator:
    def __init__(self, base_path="instance/certs"):
        """Initialize certificate generator with paths."""
        self.base_path = Path(base_path)
        self.ca_key = self.base_path / "ca.key"
        self.ca_cert = self.base_path / "ca.crt"
        self.server_key = self.base_path / "server.key"
        self.server_csr = self.base_path / "server.csr"
        self.server_cert = self.base_path / "server.crt"
        self.config_path = self.base_path / "openssl.cnf"

    def create_directories(self):
        """Create necessary directories."""
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created certificate directory: {self.base_path}")

    def create_openssl_config(self):
        """Create OpenSSL configuration file for local development."""
        config_content = """[req]
default_bits = 2048
prompt = no
default_md = sha256
distinguished_name = dn
x509_extensions = v3_req

[dn]
C = US
ST = Development State
L = Development City
O = Development Organization
OU = Development Unit
CN = localhost

[v3_req]
subjectAltName = @alt_names
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment

[alt_names]
DNS.1 = localhost
IP.1 = 127.0.0.1
"""
        with open(self.config_path, 'w') as f:
            f.write(config_content)
        logger.info(f"Created OpenSSL config at: {self.config_path}")

    def generate_ca(self):
        """Generate Certificate Authority key and certificate."""
        # Generate CA private key
        subprocess.run([
            'openssl', 'genrsa',
            '-out', str(self.ca_key),
            '2048'
        ], check=True)
        
        # Generate CA certificate
        subprocess.run([
            'openssl', 'req',
            '-x509',
            '-new',
            '-nodes',
            '-key', str(self.ca_key),
            '-sha256',
            '-days', '365',
            '-out', str(self.ca_cert),
            '-subj', '/C=US/ST=Development/L=Development/O=Development CA/CN=Development CA Root'
        ], check=True)
        
        logger.info("Generated CA key and certificate")

    def generate_server_certificate(self):
        """Generate server key and certificate signed by our CA."""
        # Generate server private key
        subprocess.run([
            'openssl', 'genrsa',
            '-out', str(self.server_key),
            '2048'
        ], check=True)

        # Generate CSR
        subprocess.run([
            'openssl', 'req',
            '-new',
            '-key', str(self.server_key),
            '-out', str(self.server_csr),
            '-config', str(self.config_path)
        ], check=True)

        # Generate certificate signed by our CA
        subprocess.run([
            'openssl', 'x509',
            '-req',
            '-in', str(self.server_csr),
            '-CA', str(self.ca_cert),
            '-CAkey', str(self.ca_key),
            '-CAcreateserial',
            '-out', str(self.server_cert),
            '-days', '365',
            '-sha256',
            '-extensions', 'v3_req',
            '-extfile', str(self.config_path)
        ], check=True)

        # Remove CSR as it's no longer needed
        self.server_csr.unlink()
        
        logger.info("Generated server key and certificate")

    def set_permissions(self):
        """Set correct permissions for generated files."""
        for file in [self.ca_key, self.server_key]:
            os.chmod(file, 0o600)
        for file in [self.ca_cert, self.server_cert]:
            os.chmod(file, 0o644)
        logger.info("Set correct file permissions")

    def generate(self):
        """Generate all necessary certificates."""
        try:
            self.create_directories()
            self.create_openssl_config()
            self.generate_ca()
            self.generate_server_certificate()
            self.set_permissions()
            logger.info("Successfully generated all certificates")
            
            # Print helpful information
            print("\nCertificates generated successfully!")
            print(f"\nCertificate locations:")
            print(f"CA Certificate: {self.ca_cert}")
            print(f"Server Certificate: {self.server_cert}")
            print(f"Server Key: {self.server_key}")
            print("\nUpdate your .env file with:")
            print(f"SSL_KEYFILE={self.server_key}")
            print(f"SSL_CERTFILE={self.server_cert}")
            print("\nFor Vault configuration, use:")
            print(f"tls_cert_file = \"{self.server_cert}\"")
            print(f"tls_key_file = \"{self.server_key}\"")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to generate certificates: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

if __name__ == "__main__":
    generator = CertificateGenerator()
    generator.generate()
