#!/usr/bin/env python
"""
Export RSA keys as base64 for Cloudflare Worker secrets.

Generates a key pair (or uses existing file-based keys) and outputs
base64-encoded values ready for `wrangler secret put`.

Usage:
    python scripts/export_rsa_keys_b64.py           # Use existing or generate
    python scripts/export_rsa_keys_b64.py --generate # Force generate new keys

Then store in CF Worker secrets (interactive — avoids shell history leak):
    npx wrangler secret put RSA_PRIVATE_KEY   # paste value when prompted
    npx wrangler secret put RSA_PUBLIC_KEY     # paste value when prompted
"""

import argparse
import base64
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.rsa_keys import key_manager


def main():
    parser = argparse.ArgumentParser(description="Export RSA keys as base64 for CF secrets")
    parser.add_argument("--generate", action="store_true", help="Force generate new keys")
    args = parser.parse_args()

    private_pem, public_pem = key_manager.initialize_keys(force_regenerate=args.generate)

    private_b64 = base64.b64encode(private_pem.encode()).decode()
    public_b64 = base64.b64encode(public_pem.encode()).decode()

    print("=== RSA_PRIVATE_KEY (base64) ===")
    print(private_b64)
    print()
    print("=== RSA_PUBLIC_KEY (base64) ===")
    print(public_b64)
    print()
    print("Store these with (interactive — paste value when prompted):")
    print("  npx wrangler secret put RSA_PRIVATE_KEY")
    print("  npx wrangler secret put RSA_PUBLIC_KEY")
    print()
    print("[WARN] Do not paste keys into shell commands — they leak into shell history.")


if __name__ == "__main__":
    main()
