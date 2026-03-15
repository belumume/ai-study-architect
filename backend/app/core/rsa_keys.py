"""
RSA key generation and management for JWT tokens
"""

import base64
import logging
import os
from pathlib import Path

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

logger = logging.getLogger(__name__)


class RSAKeyManager:
    """Manages RSA key pairs for JWT token signing"""

    def __init__(self, keys_dir: Path | None = None):
        self.keys_dir = keys_dir or Path(__file__).parent / "keys"
        self.private_key_path = self.keys_dir / "private_key.pem"
        self.public_key_path = self.keys_dir / "public_key.pem"

    def generate_key_pair(self, key_size: int = 2048) -> tuple[str, str]:
        private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=key_size, backend=default_backend()
        )

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        return private_pem.decode(), public_pem.decode()

    def save_keys(self, private_key: str, public_key: str) -> None:
        self.keys_dir.mkdir(parents=True, exist_ok=True)

        self.private_key_path.write_text(private_key)
        if os.name != "nt":
            os.chmod(self.private_key_path, 0o600)

        self.public_key_path.write_text(public_key)
        logger.info(f"RSA keys saved to {self.keys_dir}")

    def load_keys(self) -> tuple[str, str]:
        if not self.private_key_path.exists() or not self.public_key_path.exists():
            raise FileNotFoundError(f"RSA keys not found in {self.keys_dir}")

        private_key = self.private_key_path.read_text()
        public_key = self.public_key_path.read_text()
        return private_key, public_key

    def _load_keys_from_env(self) -> tuple[str, str] | None:
        """Load RSA keys from environment variables (base64-encoded PEM).

        CF Worker secrets store the keys as base64 to avoid newline issues
        in environment variables. Falls through to None if not configured.
        """
        from app.core.config import settings

        private_b64 = settings.RSA_PRIVATE_KEY
        public_b64 = settings.RSA_PUBLIC_KEY

        if not private_b64 or not public_b64:
            return None

        try:
            private_pem = base64.b64decode(private_b64).decode("utf-8")
            public_pem = base64.b64decode(public_b64).decode("utf-8")

            if "BEGIN" not in private_pem or "BEGIN" not in public_pem:
                logger.error("RSA env vars decoded but don't contain valid PEM headers")
                return None

            logger.info("RSA keys loaded from environment variables")
            return private_pem, public_pem
        except Exception as e:
            logger.error(f"Failed to decode RSA keys from env vars: {e}")
            return None

    def initialize_keys(self, force_regenerate: bool = False) -> tuple[str, str]:
        """Initialize RSA keys with priority: env vars > files > generate new.

        Production: keys come from CF Worker secrets (env vars), persisting
        across deploys. Local dev: keys come from files or are generated fresh.
        """
        if not force_regenerate:
            # Priority 1: Environment variables (production — persists across deploys)
            env_keys = self._load_keys_from_env()
            if env_keys:
                return env_keys

            # Priority 2: File-based keys (local dev)
            try:
                return self.load_keys()
            except FileNotFoundError:
                logger.info("No existing RSA keys found, generating new ones")

        # Priority 3: Generate new keys (first local dev run)
        private_key, public_key = self.generate_key_pair()
        self.save_keys(private_key, public_key)
        return private_key, public_key

    def rotate_keys(self) -> tuple[str, str]:
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
