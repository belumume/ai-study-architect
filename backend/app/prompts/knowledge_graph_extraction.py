"""
Knowledge Graph Extraction Prompts

Prompts for extracting atomic concepts and dependencies from educational content.
Used with Claude API for mastery-based learning system.
"""

# Concept types for reference
CONCEPT_TYPES = [
    "definition",     # Basic definition or terminology
    "procedure",      # Step-by-step process
    "principle",      # Fundamental rule or law
    "example",        # Concrete example or case study
    "application",    # Practical application
    "comparison",     # Comparison between concepts
]

# Difficulty levels for reference
DIFFICULTY_LEVELS = [
    "beginner",       # Entry-level, no prerequisites
    "intermediate",   # Requires some foundational knowledge
    "advanced",       # Requires solid understanding of prerequisites
    "expert",         # Mastery-level, complex integration
]


EXTRACT_CONCEPTS_PROMPT = """You are an expert educational content analyzer helping build a knowledge graph for mastery-based learning.

Your task is to extract ATOMIC, TESTABLE concepts from the provided educational content. Each concept should represent a single, discrete unit of knowledge that a student can master independently.

IMPORTANT GUIDELINES:
1. ATOMIC: Each concept should cover ONE specific idea, skill, or principle
2. TESTABLE: Each concept should be something we can verify the student has mastered
3. GRANULAR: Break down complex topics into smaller, manageable concepts
4. HIERARCHICAL: Include both foundational and advanced concepts
5. PRACTICAL: Focus on concepts students actually need to master, not just memorize

CONCEPT TYPES (choose the most appropriate):
- definition: Basic definition or terminology (e.g., "What is a variable?")
- procedure: Step-by-step process (e.g., "How to write a for loop")
- principle: Fundamental rule or law (e.g., "Variables must be declared before use")
- example: Concrete example or case study (e.g., "Using loops to process arrays")
- application: Practical application (e.g., "Implementing binary search")
- comparison: Comparison between concepts (e.g., "Arrays vs. Linked Lists")

DIFFICULTY LEVELS (be realistic about prerequisites):
- beginner: Entry-level, minimal prerequisites (e.g., "What is a variable")
- intermediate: Requires foundational knowledge (e.g., "Using functions with parameters")
- advanced: Requires solid understanding (e.g., "Implementing recursion")
- expert: Complex integration of multiple concepts (e.g., "Dynamic programming optimization")

EDUCATIONAL CONTENT:
---
{content_text}
---

EXTRACT CONCEPTS as a JSON array with the following structure:
[
  {{
    "name": "Short, clear concept name (3-8 words)",
    "description": "Detailed explanation of what the student needs to understand or be able to do (2-4 sentences)",
    "concept_type": "One of: definition, procedure, principle, example, application, comparison",
    "difficulty": "One of: beginner, intermediate, advanced, expert",
    "estimated_minutes": 10-60,  // Realistic time to master this concept
    "keywords": ["keyword1", "keyword2", "keyword3"],  // 3-5 searchable keywords
    "examples": [  // 2-3 concrete examples that demonstrate this concept
      "Example 1: Brief, specific example",
      "Example 2: Brief, specific example"
    ]
  }}
]

QUALITY CHECKLIST:
- [ ] Each concept is atomic (covers ONE idea)
- [ ] Each concept is testable (we can verify mastery)
- [ ] Descriptions are clear and instructional
- [ ] Difficulty levels reflect actual prerequisites
- [ ] Estimated time is realistic (10-60 minutes per concept)
- [ ] Keywords are searchable and relevant
- [ ] Examples are specific and helpful

Extract 5-15 concepts depending on content complexity. Focus on quality over quantity.

Return ONLY the JSON array, no additional text."""


EXTRACT_DEPENDENCIES_PROMPT = """You are an expert curriculum designer helping build prerequisite relationships for a mastery-based learning system.

Your task is to identify PREREQUISITE RELATIONSHIPS between concepts. These dependencies determine the optimal learning path.

IMPORTANT GUIDELINES:
1. NECESSARY PREREQUISITES: Only mark dependencies that are truly required
2. DIRECT DEPENDENCIES: Don't include transitive dependencies (if A→B and B→C, don't add A→C)
3. STRENGTH RATING: Use 0.0-1.0 to indicate how critical the prerequisite is
4. MASTERY-FOCUSED: Students must master prerequisites before unlocking dependent concepts

STRENGTH LEVELS:
- 1.0: REQUIRED - Absolutely must master prerequisite first (e.g., "variables" before "functions")
- 0.7-0.9: STRONGLY RECOMMENDED - Very helpful to know first (e.g., "arrays" before "sorting algorithms")
- 0.4-0.6: RECOMMENDED - Beneficial but not critical (e.g., "basic math" before "algorithmic complexity")
- 0.1-0.3: OPTIONAL - Slightly related, minimal benefit (e.g., "command line basics" before "Python basics")

CONCEPTS:
{concepts_json}

ANALYZE PREREQUISITES and return a JSON array with the following structure:
[
  {{
    "prerequisite_name": "Name of concept that must be learned first",
    "dependent_name": "Name of concept that requires the prerequisite",
    "strength": 0.8,  // 0.0-1.0 indicating how critical this prerequisite is
    "reason": "Brief explanation of why this prerequisite is needed (1-2 sentences)"
  }}
]

QUALITY CHECKLIST:
- [ ] Only include truly necessary prerequisites
- [ ] No transitive dependencies (keep graph minimal)
- [ ] Strength ratings accurately reflect importance
- [ ] Reasons clearly explain the dependency
- [ ] No circular dependencies (A→B→A)
- [ ] No self-dependencies (A→A)

EXAMPLES OF GOOD DEPENDENCIES:
✓ "Variables in Python" → "Functions in Python" (strength: 1.0)
  Reason: "Functions use variables to store parameters and return values"

✓ "For Loops" → "Nested Loops" (strength: 1.0)
  Reason: "Nested loops are loops inside loops, requiring mastery of basic loop syntax"

✓ "Arrays" → "Sorting Algorithms" (strength: 0.8)
  Reason: "Sorting algorithms operate on arrays, so understanding array structure is essential"

EXAMPLES OF BAD DEPENDENCIES (DON'T DO THIS):
✗ "Variables" → "Sorting Algorithms" (too distant, transitive)
✗ "Basic Math" → "Variables" (strength too low, not truly required)
✗ "Functions" → "Variables" (backwards, should be Variables → Functions)

Return ONLY the JSON array, no additional text.
If there are no meaningful dependencies, return an empty array []."""


EXTRACT_COMBINED_PROMPT = """You are an expert educational content analyzer building a complete knowledge graph for mastery-based learning.

Your task is to:
1. Extract ATOMIC, TESTABLE concepts from educational content
2. Identify PREREQUISITE RELATIONSHIPS between those concepts

This will create a complete knowledge graph showing the optimal learning path.

EDUCATIONAL CONTENT:
---
{content_text}
---

PART 1: EXTRACT CONCEPTS
Extract 5-15 atomic concepts. Each concept should:
- Be TESTABLE (we can verify student mastery)
- Be ATOMIC (one clear idea)
- Have realistic difficulty and time estimates

PART 2: IDENTIFY DEPENDENCIES
Analyze the extracted concepts and identify prerequisite relationships:
- Only NECESSARY prerequisites (not "nice to have")
- DIRECT dependencies only (no transitive chains)
- Accurate STRENGTH ratings (0.0-1.0)

OUTPUT FORMAT (JSON):
{{
  "concepts": [
    {{
      "name": "Concept name",
      "description": "What student needs to understand/do",
      "concept_type": "definition|procedure|principle|example|application|comparison",
      "difficulty": "beginner|intermediate|advanced|expert",
      "estimated_minutes": 15,
      "keywords": ["keyword1", "keyword2"],
      "examples": ["Example 1", "Example 2"]
    }}
  ],
  "dependencies": [
    {{
      "prerequisite_name": "Concept learned first",
      "dependent_name": "Concept requiring prerequisite",
      "strength": 0.8,
      "reason": "Why this prerequisite is needed"
    }}
  ]
}}

QUALITY STANDARDS:
✓ Concepts are atomic and testable
✓ Difficulty levels reflect actual prerequisites
✓ Time estimates are realistic (10-60 min per concept)
✓ Dependencies are necessary and direct
✓ No circular or self-dependencies
✓ Strength ratings match importance

Return ONLY the JSON object, no additional text."""


def format_concepts_for_dependency_extraction(concepts: list[dict]) -> str:
    """
    Format extracted concepts for the dependency extraction prompt

    Args:
        concepts: List of concept dictionaries from concept extraction

    Returns:
        Formatted string listing concepts for dependency analysis
    """
    formatted = []
    for i, concept in enumerate(concepts, 1):
        formatted.append(
            f"{i}. {concept['name']}\n"
            f"   Type: {concept['concept_type']}\n"
            f"   Difficulty: {concept['difficulty']}\n"
            f"   Description: {concept['description']}"
        )
    return "\n\n".join(formatted)


def validate_extraction_response(response: dict) -> tuple[bool, list[str]]:
    """
    Validate the structure of an extraction response

    Args:
        response: The parsed JSON response from concept extraction

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    # Check top-level structure for combined extraction
    if "concepts" in response and "dependencies" in response:
        concepts = response["concepts"]
        dependencies = response["dependencies"]
    # Handle concepts-only extraction
    elif isinstance(response, list):
        concepts = response
        dependencies = []
    else:
        return False, ["Invalid response structure: expected object with 'concepts' and 'dependencies' or array of concepts"]

    # Validate concepts
    if not isinstance(concepts, list):
        errors.append("'concepts' must be an array")
    else:
        for i, concept in enumerate(concepts):
            if not isinstance(concept, dict):
                errors.append(f"Concept {i} must be an object")
                continue

            # Required fields
            required = ["name", "description", "concept_type", "difficulty"]
            for field in required:
                if field not in concept:
                    errors.append(f"Concept {i} missing required field: {field}")

            # Validate enums
            if "concept_type" in concept and concept["concept_type"] not in CONCEPT_TYPES:
                errors.append(f"Concept {i} has invalid concept_type: {concept['concept_type']}")

            if "difficulty" in concept and concept["difficulty"] not in DIFFICULTY_LEVELS:
                errors.append(f"Concept {i} has invalid difficulty: {concept['difficulty']}")

            # Validate estimated_minutes range
            if "estimated_minutes" in concept:
                minutes = concept["estimated_minutes"]
                if not isinstance(minutes, (int, float)) or minutes < 0 or minutes > 480:
                    errors.append(f"Concept {i} estimated_minutes must be between 0 and 480")

    # Validate dependencies
    if not isinstance(dependencies, list):
        errors.append("'dependencies' must be an array")
    else:
        concept_names = {c.get("name") for c in concepts if isinstance(c, dict)}

        for i, dep in enumerate(dependencies):
            if not isinstance(dep, dict):
                errors.append(f"Dependency {i} must be an object")
                continue

            # Required fields
            required = ["prerequisite_name", "dependent_name", "strength"]
            for field in required:
                if field not in dep:
                    errors.append(f"Dependency {i} missing required field: {field}")

            # Validate concept references
            if "prerequisite_name" in dep and dep["prerequisite_name"] not in concept_names:
                errors.append(f"Dependency {i} references unknown prerequisite: {dep['prerequisite_name']}")

            if "dependent_name" in dep and dep["dependent_name"] not in concept_names:
                errors.append(f"Dependency {i} references unknown dependent: {dep['dependent_name']}")

            # Validate strength range
            if "strength" in dep:
                strength = dep["strength"]
                if not isinstance(strength, (int, float)) or strength < 0.0 or strength > 1.0:
                    errors.append(f"Dependency {i} strength must be between 0.0 and 1.0")

            # Check for self-dependencies
            if dep.get("prerequisite_name") == dep.get("dependent_name"):
                errors.append(f"Dependency {i} is a self-dependency (concept depends on itself)")

    return len(errors) == 0, errors


def get_extraction_prompt(
    content_text: str,
    mode: str = "combined"
) -> str:
    """
    Get the appropriate extraction prompt based on mode

    Args:
        content_text: The educational content to analyze
        mode: "concepts", "dependencies", or "combined"

    Returns:
        Formatted prompt string
    """
    if mode == "concepts":
        return EXTRACT_CONCEPTS_PROMPT.format(content_text=content_text)
    elif mode == "combined":
        return EXTRACT_COMBINED_PROMPT.format(content_text=content_text)
    else:
        raise ValueError(f"Invalid mode: {mode}. Use 'concepts', 'dependencies', or 'combined'")
