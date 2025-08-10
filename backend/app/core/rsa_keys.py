"""
RSA key generation and management for JWT tokens
"""

import os
from pathlib import Path
from typing import Tuple, Optional
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import logging

logger = logging.getLogger(__name__)


class RSAKeyManager:
    """Manages RSA key pairs for JWT token signing"""
    
    def __init__(self, keys_dir: Optional[Path] = None):
        """
        Initialize RSA key manager
        
        Args:
            keys_dir: Directory to store keys (default: app/core/keys)
        """
        self.keys_dir = keys_dir or Path(__file__).parent / "keys"
        self.private_key_path = self.keys_dir / "private_key.pem"
        self.public_key_path = self.keys_dir / "public_key.pem"
        
    def generate_key_pair(self, key_size: int = 2048) -> Tuple[str, str]:
        """
        Generate a new RSA key pair
        
        Args:
            key_size: Size of the key in bits (default: 2048)
            
        Returns:
            Tuple of (private_key_pem, public_key_pem)
        """
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend()
        )
        
        # Get private key in PEM format
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # Get public key
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return private_pem.decode(), public_pem.decode()
    
    def save_keys(self, private_key: str, public_key: str) -> None:
        """
        Save RSA keys to files
        
        Args:
            private_key: Private key in PEM format
            public_key: Public key in PEM format
        """
        # Create keys directory if it doesn't exist
        self.keys_dir.mkdir(parents=True, exist_ok=True)
        
        # Set restrictive permissions for private key
        self.private_key_path.write_text(private_key)
        if os.name != 'nt':  # Not Windows
            os.chmod(self.private_key_path, 0o600)
        
        # Save public key
        self.public_key_path.write_text(public_key)
        
        logger.info(f"RSA keys saved to {self.keys_dir}")
    
    def load_keys(self) -> Tuple[str, str]:
        """
        Load RSA keys from files
        
        Returns:
            Tuple of (private_key_pem, public_key_pem)
            
        Raises:
            FileNotFoundError: If key files don't exist
        """
        if not self.private_key_path.exists() or not self.public_key_path.exists():
            raise FileNotFoundError(f"RSA keys not found in {self.keys_dir}")
        
        private_key = self.private_key_path.read_text()
        public_key = self.public_key_path.read_text()
        
        return private_key, public_key
    
    def initialize_keys(self, force_regenerate: bool = False) -> Tuple[str, str]:
        """
        Initialize RSA keys - load existing or generate new ones
        
        Args:
            force_regenerate: Force generation of new keys
            
        Returns:
            Tuple of (private_key_pem, public_key_pem)
        """
        if not force_regenerate:
            try:
                return self.load_keys()
            except FileNotFoundError:
                logger.info("No existing RSA keys found, generating new ones")
        
        # Generate new keys
        private_key, public_key = self.generate_key_pair()
        self.save_keys(private_key, public_key)
        
        return private_key, public_key
    
    def rotate_keys(self) -> Tuple[str, str]:
        """
        Rotate RSA keys by generating new ones and archiving old ones
        
        Returns:
            Tuple of new (private_key_pem, public_key_pem)
        """
        # Archive existing keys if they exist
        if self.private_key_path.exists():
            import time
            timestamp = int(time.time())
            archive_dir = self.keys_dir / "archive"
            archive_dir.mkdir(exist_ok=True)
            
            # Move old keys to archive with Windows compatibility
            private_archive_path = archive_dir / f"private_key_{timestamp}.pem"
            public_archive_path = archive_dir / f"public_key_{timestamp}.pem"
            
            # Handle Windows file existence issues
            if private_archive_path.exists():
                private_archive_path.unlink()
            if public_archive_path.exists():
                public_archive_path.unlink()
            
            old_private = self.private_key_path.rename(private_archive_path)
            old_public = self.public_key_path.rename(public_archive_path)
            
            logger.info(f"Archived old keys to {archive_dir}")
        
        # Generate new keys
        return self.initialize_keys(force_regenerate=True)


# Singleton instance
key_manager = RSAKeyManager()