"""
Spike: Compare Sonnet vs Haiku concept extraction quality.

Tests both models with realistic academic content and compares:
- Number of concepts extracted
- Quality of SVO names
- Accuracy of difficulty ratings
- Extraction confidence

Run: cd backend && python tests/spike_model_comparison.py
"""

import asyncio
import json
import os
import time
from pathlib import Path

import httpx

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

# Inline the schema and prompt to avoid importing the full app (which needs pg8000)
EXTRACTION_SYSTEM_PROMPT = """You are a concept extraction engine for an educational platform.
Extract atomic learning concepts from study material as Subject-Verb-Object (SVO) learning objectives.

For each concept, provide:
- name: Clear SVO learning objective (3-10 words)
- description: Concise explanation (1-3 sentences)
- concept_type: definition | procedure | principle | example | application | comparison
- difficulty: beginner | intermediate | advanced | expert
- estimated_minutes: Time to master (5-60 minutes)
- keywords: 3-5 related search terms
- examples: 1-2 example questions testing this concept

Also identify prerequisite dependencies between extracted concepts."""

CONCEPT_EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "concepts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "concept_type": {
                        "type": "string",
                        "enum": [
                            "definition",
                            "procedure",
                            "principle",
                            "example",
                            "application",
                            "comparison",
                        ],
                    },
                    "difficulty": {
                        "type": "string",
                        "enum": ["beginner", "intermediate", "advanced", "expert"],
                    },
                    "estimated_minutes": {"type": "integer"},
                    "keywords": {"type": "array", "items": {"type": "string"}},
                    "examples": {"type": "array", "items": {"type": "string"}},
                },
                "required": [
                    "name",
                    "description",
                    "concept_type",
                    "difficulty",
                    "estimated_minutes",
                    "keywords",
                    "examples",
                ],
                "additionalProperties": False,
            },
        },
        "dependencies": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "prerequisite_name": {"type": "string"},
                    "dependent_name": {"type": "string"},
                    "strength": {"type": "number"},
                    "reason": {"type": "string"},
                },
                "required": ["prerequisite_name", "dependent_name", "strength", "reason"],
                "additionalProperties": False,
            },
        },
        "metadata": {
            "type": "object",
            "properties": {
                "total_extracted": {"type": "integer"},
                "extraction_confidence": {"type": "number"},
                "notes": {"type": "string"},
            },
            "required": ["total_extracted", "extraction_confidence", "notes"],
            "additionalProperties": False,
        },
    },
    "required": ["concepts", "dependencies", "metadata"],
    "additionalProperties": False,
}

ACADEMIC_TEXT = """
Chapter 3: Hash Tables and Hash Functions

A hash table is a data structure that implements an associative array, mapping keys to values.
It uses a hash function to compute an index into an array of buckets or slots.

Hash Functions:
A good hash function should satisfy the simple uniform hashing assumption (SUHA):
each key is equally likely to hash to any of the m slots. Common hash functions include:
- Division method: h(k) = k mod m
- Multiplication method: h(k) = floor(m * (k*A mod 1)) where 0 < A < 1
- Universal hashing: randomly select h from a family H of hash functions

Collision Resolution:
When two keys hash to the same slot, we have a collision. Two main strategies:

1. Chaining (Open Hashing): Each slot contains a linked list of elements.
   - Average case O(1+alpha) for search, where alpha = n/m is the load factor
   - Worst case O(n) if all elements hash to the same slot

2. Open Addressing (Closed Hashing): All elements stored in the hash table itself.
   - Linear probing: h(k,i) = (h'(k) + i) mod m — suffers from primary clustering
   - Quadratic probing: h(k,i) = (h'(k) + c1*i + c2*i^2) mod m
   - Double hashing: h(k,i) = (h1(k) + i*h2(k)) mod m — best distribution

Performance Analysis:
For a hash table with load factor alpha:
- Chaining: Expected number of probes for unsuccessful search = 1 + alpha
- Open addressing (uniform hashing): Expected probes = 1/(1-alpha)
- As alpha approaches 1, open addressing degrades severely

Perfect Hashing:
When the set of keys is known in advance, we can achieve O(1) worst-case lookup
using a two-level scheme (Fredman, Komlos, Szemeredi 1984).
"""


async def extract_with_model(model: str) -> dict:
    payload = {
        "model": model,
        "max_tokens": 4096,
        "temperature": 0.15,
        "system": [{"type": "text", "text": EXTRACTION_SYSTEM_PROMPT}],
        "messages": [
            {
                "role": "user",
                "content": f"Extract concepts from this study material:\n\n{ACADEMIC_TEXT}",
            }
        ],
        "output_config": {
            "format": {
                "type": "json_schema",
                "schema": CONCEPT_EXTRACTION_SCHEMA,
            }
        },
    }

    start = time.monotonic()
    async with httpx.AsyncClient(timeout=httpx.Timeout(90.0, connect=5.0)) as client:
        response = await client.post(f"{BASE_URL}/messages", headers=HEADERS, json=payload)
    elapsed = time.monotonic() - start

    if response.status_code != 200:
        return {"model": model, "error": response.text[:300]}

    data = response.json()
    parsed = json.loads(data["content"][0]["text"])

    return {
        "model": model,
        "elapsed": round(elapsed, 2),
        "input_tokens": data["usage"]["input_tokens"],
        "output_tokens": data["usage"]["output_tokens"],
        "concepts": parsed.get("concepts", []),
        "dependencies": parsed.get("dependencies", []),
        "metadata": parsed.get("metadata", {}),
    }


async def main():
    if not API_KEY:
        print("[FAIL] ANTHROPIC_API_KEY not set")
        return

    print("=" * 70)
    print("MODEL COMPARISON: Concept Extraction Quality")
    print("=" * 70)

    models = ["claude-sonnet-4-6", "claude-haiku-4-5"]
    results = await asyncio.gather(*[extract_with_model(m) for m in models])

    for r in results:
        if "error" in r:
            print(f"\n{r['model']}: ERROR - {r['error']}")
            continue

        print(f"\n{'=' * 50}")
        print(f"Model: {r['model']}")
        print(f"Time: {r['elapsed']}s | Tokens: {r['input_tokens']} in / {r['output_tokens']} out")
        print(f"Concepts: {len(r['concepts'])} | Dependencies: {len(r['dependencies'])}")
        print(f"Confidence: {r['metadata'].get('extraction_confidence', '?')}")
        print(f"{'-' * 50}")

        for c in r["concepts"]:
            print(f"  [{c['difficulty'][:3].upper()}] {c['concept_type']:<12} {c['name']}")

        if r["dependencies"]:
            print("\n  Dependencies:")
            for d in r["dependencies"][:5]:
                print(f"    {d['prerequisite_name']} -> {d['dependent_name']} ({d['strength']})")

    # Cost comparison
    print(f"\n{'=' * 70}")
    print("COST COMPARISON (per extraction)")
    for r in results:
        if "error" in r:
            continue
        in_cost = r["input_tokens"] / 1_000_000
        out_cost = r["output_tokens"] / 1_000_000
        if "sonnet" in r["model"]:
            total = in_cost * 3 + out_cost * 15
        else:
            total = in_cost * 1 + out_cost * 5
        print(f"  {r['model']}: ${total:.4f}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
