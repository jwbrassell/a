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

def generate_ca_cert(cert_dir):
    """Generate CA certificate and private key."""
    ca_key = cert_dir / "ca.key"
    ca_cert = cert_dir / "ca.crt"
    
    # Generate CA private key
    subprocess.run([
        "openssl", "genrsa",
        "-out", str(ca_key),
        "4096"
    ], check=True)
    
    # Generate CA certificate
    subprocess.run([
        "openssl", "req",
        "-x509",
        "-new",
        "-nodes",
        "-key", str(ca_key),
        "-sha256",
        "-days", "365",
        "-out", str(ca_cert),
        "-subj", "/C=US/ST=State/L=City/O=Organization/CN=Development CA"
    ], check=True)
    
    return ca_key, ca_cert

def generate_server_cert(cert_dir, ca_key, ca_cert):
    """Generate server certificate signed by the CA."""
    server_key = cert_dir / "server.key"
    server_csr = cert_dir / "server.csr"
    server_cert = cert_dir / "server.crt"
    
    # Generate server private key
    subprocess.run([
        "openssl", "genrsa",
        "-out", str(server_key),
        "2048"
    ], check=True)
    
    # Generate CSR
    subprocess.run([
        "openssl", "req",
        "-new",
        "-key", str(server_key),
        "-out", str(server_csr),
        "-subj", "/C=US/ST=State/L=City/O=Organization/CN=localhost"
    ], check=True)
    
    # Create server certificate extensions file
    ext_file = cert_dir / "server.ext"
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
        "-CA", str(ca_cert),
        "-CAkey", str(ca_key),
        "-CAcreateserial",
        "-out", str(server_cert),
        "-days", "365",
        "-sha256",
        "-extfile", str(ext_file)
    ], check=True)
    
    # Clean up CSR and extensions file
    server_csr.unlink()
    ext_file.unlink()
    
    return server_key, server_cert

def setup_dev_certificates():
    """Set up development certificates."""
    try:
        # Create certificates directory
        cert_dir = Path("certs")
        cert_dir.mkdir(exist_ok=True)
        
        logger.info("Generating CA certificate...")
        ca_key, ca_cert = generate_ca_cert(cert_dir)
        
        logger.info("Generating server certificate...")
        server_key, server_cert = generate_server_cert(cert_dir, ca_key, ca_cert)
        
        # Set appropriate permissions
        for cert_file in [ca_key, ca_cert, server_key, server_cert]:
            os.chmod(cert_file, 0o600)
        
        logger.info(
            f"\nDevelopment certificates generated successfully:\n"
            f"CA Certificate: {ca_cert}\n"
            f"Server Certificate: {server_cert}\n"
            f"Server Key: {server_key}\n\n"
            f"To use these certificates:\n"
            f"1. Set the following environment variables:\n"
            f"   export VAULT_CACERT={ca_cert.resolve()}\n"
            f"   export VAULT_CLIENT_CERT={server_cert.resolve()}\n"
            f"   export VAULT_CLIENT_KEY={server_key.resolve()}\n\n"
            f"2. Update your Vault configuration to use TLS:\n"
            f"   listener \"tcp\" {{\n"
            f"     address     = \"127.0.0.1:8200\"\n"
            f"     tls_cert_file = \"{server_cert.resolve()}\"\n"
            f"     tls_key_file  = \"{server_key.resolve()}\"\n"
            f"   }}\n"
        )
        
        return {
            "ca_cert": str(ca_cert.resolve()),
            "server_cert": str(server_cert.resolve()),
            "server_key": str(server_key.resolve())
        }
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to generate certificates: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error while generating certificates: {e}")
        raise

if __name__ == "__main__":
    setup_dev_certificates()
