"""
Spike test: Validate Claude Structured Outputs works with raw httpx.

Tests that output_config.format with json_schema returns guaranteed valid JSON
using the project's existing headers (anthropic-version: 2023-06-01).

Run: cd backend && python tests/spike_structured_outputs.py
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path

import httpx

# Load .env manually (no dependency on dotenv)
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

API_KEY = os.environ.get("ANTHROPIC_API_KEY")
BASE_URL = "https://api.anthropic.com/v1"

HEADERS = {
    "x-api-key": API_KEY,
    "anthropic-version": "2023-06-01",
    "content-type": "application/json",
}

# Simple schema for testing
TEST_SCHEMA = {
    "type": "object",
    "properties": {
        "concepts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "difficulty": {
                        "type": "string",
                        "enum": ["beginner", "intermediate", "advanced"],
                    },
                },
                "required": ["name", "description", "difficulty"],
                "additionalProperties": False,
            },
        },
        "total": {"type": "integer"},
    },
    "required": ["concepts", "total"],
    "additionalProperties": False,
}

SAMPLE_TEXT = """
Binary search is an efficient algorithm for finding a target value in a sorted array.
It works by repeatedly dividing the search interval in half.
Time complexity is O(log n). It requires the array to be sorted first.
A common mistake is applying binary search to unsorted data.
"""


async def test_model(model: str) -> dict:
    """Test structured outputs with a specific model."""
    payload = {
        "model": model,
        "max_tokens": 1024,
        "temperature": 0.1,
        "messages": [
            {
                "role": "user",
                "content": f"Extract concepts from this text:\n\n{SAMPLE_TEXT}",
            }
        ],
        "output_config": {
            "format": {
                "type": "json_schema",
                "schema": TEST_SCHEMA,
            }
        },
    }

    start = time.monotonic()
    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=5.0)) as client:
        response = await client.post(
            f"{BASE_URL}/messages",
            headers=HEADERS,
            json=payload,
        )

    elapsed = time.monotonic() - start

    result = {
        "model": model,
        "status_code": response.status_code,
        "elapsed_seconds": round(elapsed, 2),
    }

    if response.status_code != 200:
        result["error"] = response.text[:500]
        return result

    data = response.json()
    raw_text = data["content"][0]["text"]

    # Test 1: json.loads parses cleanly
    try:
        parsed = json.loads(raw_text)
        result["json_valid"] = True
    except json.JSONDecodeError as e:
        result["json_valid"] = False
        result["json_error"] = str(e)
        return result

    # Test 2: Schema compliance checks
    result["has_concepts"] = "concepts" in parsed
    result["has_total"] = "total" in parsed
    result["concept_count"] = len(parsed.get("concepts", []))
    result["total_field"] = parsed.get("total")

    # Test 3: Each concept has required fields
    all_valid = True
    for c in parsed.get("concepts", []):
        if not all(k in c for k in ("name", "description", "difficulty")):
            all_valid = False
        if c.get("difficulty") not in ("beginner", "intermediate", "advanced"):
            all_valid = False
    result["all_concepts_valid"] = all_valid

    # Test 4: No extra fields (additionalProperties: false)
    extra_keys = set(parsed.keys()) - {"concepts", "total"}
    result["no_extra_fields"] = len(extra_keys) == 0
    if extra_keys:
        result["extra_keys"] = list(extra_keys)

    # Usage info
    result["input_tokens"] = data.get("usage", {}).get("input_tokens")
    result["output_tokens"] = data.get("usage", {}).get("output_tokens")
    result["stop_reason"] = data.get("stop_reason")

    # Sample output
    result["sample_concept"] = parsed["concepts"][0] if parsed.get("concepts") else None

    return result


async def main():
    if not API_KEY:
        print("[FAIL] ANTHROPIC_API_KEY not set")
        sys.exit(1)

    print("=" * 60)
    print("SPIKE: Claude Structured Outputs via raw httpx")
    print("=" * 60)

    models = ["claude-sonnet-4-6", "claude-haiku-4-5"]

    for model in models:
        print(f"\n--- Testing {model} ---")
        try:
            result = await test_model(model)
        except Exception as e:
            print(f"  [FAIL] Exception: {e}")
            continue

        if result["status_code"] != 200:
            print(f"  [FAIL] HTTP {result['status_code']}: {result.get('error', '')}")
            continue

        checks = [
            ("HTTP 200", result["status_code"] == 200),
            ("JSON valid", result.get("json_valid", False)),
            ("Has concepts[]", result.get("has_concepts", False)),
            ("Has total field", result.get("has_total", False)),
            ("All concepts valid", result.get("all_concepts_valid", False)),
            ("No extra fields", result.get("no_extra_fields", False)),
        ]

        all_pass = True
        for name, passed in checks:
            status = "[PASS]" if passed else "[FAIL]"
            if not passed:
                all_pass = False
            print(f"  {status} {name}")

        print(f"  Concepts extracted: {result.get('concept_count', 0)}")
        print(
            f"  Tokens: {result.get('input_tokens', '?')} in / {result.get('output_tokens', '?')} out"
        )
        print(f"  Time: {result['elapsed_seconds']}s")
        print(f"  Stop reason: {result.get('stop_reason')}")

        if result.get("sample_concept"):
            c = result["sample_concept"]
            print(f'  Sample: "{c["name"]}" ({c["difficulty"]})')

        if all_pass:
            print(f"  >>> ALL CHECKS PASSED for {model}")
        else:
            print(f"  >>> SOME CHECKS FAILED for {model}")

    print("\n" + "=" * 60)
    print("SPIKE COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
