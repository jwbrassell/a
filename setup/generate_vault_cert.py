#!/usr/bin/env python3
import os
from pathlib import Path
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta
import logging
import ipaddress

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_vault_certificate(cert_dir):
    """Generate a self-signed certificate for Vault."""
    try:
        # Create directory if it doesn't exist
        cert_dir = Path(cert_dir)
        cert_dir.mkdir(parents=True, mode=0o700, exist_ok=True)
        
        # Generate key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        
        # Generate certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, u"localhost"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Local Vault"),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, u"Development"),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName(u"localhost"),
                x509.IPAddress(ipaddress.IPv4Address(u"127.0.0.1"))
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256())
        
        # Save certificate
        cert_path = cert_dir / "vault-ca.pem"
        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        os.chmod(cert_path, 0o600)
        
        # Save private key
        key_path = cert_dir / "vault-ca-key.pem"
        with open(key_path, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        os.chmod(key_path, 0o600)
        
        logger.info(f"Generated certificate at {cert_path}")
        logger.info(f"Generated private key at {key_path}")
        
        return str(cert_path)
    except Exception as e:
        logger.error(f"Failed to generate certificate: {e}")
        raise

def setup_vault_certificates():
    """Setup Vault certificates in the instance directory."""
    try:
        # Get the app's root path
        root_path = Path(__file__).parent.parent
        instance_path = root_path / "instance"
        cert_dir = instance_path / "certs"
        
        # Generate certificate
        cert_path = generate_vault_certificate(cert_dir)
        
        # Update .env file
        env_path = root_path / ".env"
        env_content = f"""
# Vault Certificate Configuration
VAULT_CACERT={cert_path}
"""
        
        # Append to .env file if it exists, create if it doesn't
        mode = 'a' if env_path.exists() else 'w'
        with open(env_path, mode) as f:
            f.write(env_content)
        
        logger.info("Successfully configured Vault certificates")
        logger.info(f"Certificate path added to {env_path}")
        
    except Exception as e:
        logger.error(f"Failed to setup Vault certificates: {e}")
        raise

if __name__ == "__main__":
    setup_vault_certificates()
