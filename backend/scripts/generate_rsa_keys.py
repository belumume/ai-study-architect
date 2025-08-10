#!/usr/bin/env python
"""
Generate RSA keys for JWT token signing

Usage:
    python scripts/generate_rsa_keys.py [--force]
"""

import sys
import argparse
import logging
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.rsa_keys import key_manager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Generate RSA keys for JWT signing")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force regeneration of keys even if they exist"
    )
    parser.add_argument(
        "--rotate",
        action="store_true",
        help="Rotate keys (archive old ones and generate new)"
    )
    
    args = parser.parse_args()
    
    try:
        if args.rotate:
            logger.info("Rotating RSA keys...")
            private_key, public_key = key_manager.rotate_keys()
            logger.info("Keys rotated successfully!")
        else:
            logger.info("Generating RSA keys...")
            private_key, public_key = key_manager.initialize_keys(
                force_regenerate=args.force
            )
            logger.info("Keys generated successfully!")
        
        logger.info(f"Keys saved to: {key_manager.keys_dir}")
        logger.info(f"Private key: {key_manager.private_key_path}")
        logger.info(f"Public key: {key_manager.public_key_path}")
        
        # Show public key for documentation
        logger.info("Public key (can be shared):")
        logger.info(public_key)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()