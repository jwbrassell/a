#!/usr/bin/env python3
import os
import subprocess
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CertificateGenerator:
    """Generate development certificates for Vault."""
    
    def __init__(self, cert_dir="certs"):
        self.cert_dir = Path(cert_dir)
        self.cert_dir.mkdir(exist_ok=True)
        self.ca_key = self.cert_dir / "ca.key"
        self.ca_cert = self.cert_dir / "ca.crt"
        self.server_key = self.cert_dir / "server.key"
        self.server_cert = self.cert_dir / "server.crt"
    
    def generate_ca_cert(self):
        """Generate CA certificate and private key."""
        # Generate CA private key
        subprocess.run([
            "openssl", "genrsa",
            "-out", str(self.ca_key),
            "4096"
        ], check=True)
        
        # Generate CA certificate
        subprocess.run([
            "openssl", "req",
            "-x509",
            "-new",
            "-nodes",
            "-key", str(self.ca_key),
            "-sha256",
            "-days", "365",
            "-out", str(self.ca_cert),
            "-subj", "/C=US/ST=State/L=City/O=Organization/CN=Development CA"
        ], check=True)
        
        return self.ca_key, self.ca_cert
    
    def generate_server_cert(self):
        """Generate server certificate signed by the CA."""
        server_csr = self.cert_dir / "server.csr"
        
        # Generate server private key
        subprocess.run([
            "openssl", "genrsa",
            "-out", str(self.server_key),
            "2048"
        ], check=True)
        
        # Generate CSR
        subprocess.run([
            "openssl", "req",
            "-new",
            "-key", str(self.server_key),
            "-out", str(server_csr),
            "-subj", "/C=US/ST=State/L=City/O=Organization/CN=localhost"
        ], check=True)
        
        # Create server certificate extensions file
        ext_file = self.cert_dir / "server.ext"
        with open(ext_file, 'w') as f:
            f.write("""authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
IP.1 = 127.0.0.1""")
        
        # Sign the CSR with CA
        subprocess.run([
            "openssl", "x509",
            "-req",
            "-in", str(server_csr),
            "-CA", str(self.ca_cert),
            "-CAkey", str(self.ca_key),
            "-CAcreateserial",
            "-out", str(self.server_cert),
            "-days", "365",
            "-sha256",
            "-extfile", str(ext_file)
        ], check=True)
        
        # Clean up CSR and extensions file
        server_csr.unlink()
        ext_file.unlink()
        
        return self.server_key, self.server_cert
    
    def setup_certificates(self):
        """Set up development certificates."""
        try:
            logger.info("Generating CA certificate...")
            self.generate_ca_cert()
            
            logger.info("Generating server certificate...")
            self.generate_server_cert()
            
            # Set appropriate permissions
            for cert_file in [self.ca_key, self.ca_cert, self.server_key, self.server_cert]:
                os.chmod(cert_file, 0o600)
            
            logger.info(
                f"\nDevelopment certificates generated successfully:\n"
                f"CA Certificate: {self.ca_cert}\n"
                f"Server Certificate: {self.server_cert}\n"
                f"Server Key: {self.server_key}\n\n"
                f"To use these certificates:\n"
                f"1. Set the following environment variables:\n"
                f"   export VAULT_CACERT={self.ca_cert.resolve()}\n"
                f"   export VAULT_CLIENT_CERT={self.server_cert.resolve()}\n"
                f"   export VAULT_CLIENT_KEY={self.server_key.resolve()}\n\n"
                f"2. Update your Vault configuration to use TLS:\n"
                f"   listener \"tcp\" {{\n"
                f"     address     = \"127.0.0.1:8200\"\n"
                f"     tls_cert_file = \"{self.server_cert.resolve()}\"\n"
                f"     tls_key_file  = \"{self.server_key.resolve()}\"\n"
                f"   }}\n"
            )
            
            return {
                "ca_cert": str(self.ca_cert.resolve()),
                "server_cert": str(self.server_cert.resolve()),
                "server_key": str(self.server_key.resolve())
            }
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to generate certificates: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while generating certificates: {e}")
            raise

def setup_dev_certificates():
    """Helper function to set up development certificates."""
    generator = CertificateGenerator()
    return generator.setup_certificates()

if __name__ == "__main__":
    setup_dev_certificates()
