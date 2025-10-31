"""
NLU Module - Natural Language Understanding with LLM Function Calling

This demonstrates how modern LLM-based NLU differs from traditional
intent/slot models (like Alexa). No training data needed!
"""

import json
import os
from typing import Dict, List, Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# Define the function schema (like Alexa intent schema, but more flexible)
SEARCH_FUNCTION_SCHEMA = {
    "name": "search_products",
    "description": "Search for pet products based on user criteria",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query (what the user is looking for)"
            },
            "target_pet": {
                "type": "string",
                "enum": ["dog", "cat", "bird", "fish"],
                "description": "Type of pet the product is for"
            },
            "dietary_exclusions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Ingredients to EXCLUDE. Extract from terms like 'salmon-free', 'grain-free', 'without chicken', 'no beef', etc."
            },
            "dietary_requirements": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Positive dietary requirements like 'high-protein', 'organic', 'limited-ingredient'"
            },
            "price_max": {
                "type": "number",
                "description": "Maximum price in dollars"
            },
            "price_min": {
                "type": "number",
                "description": "Minimum price in dollars"
            },
            "life_stage": {
                "type": "string",
                "enum": ["puppy", "adult", "senior", "all"],
                "description": "Life stage of the pet"
            },
            "size_category": {
                "type": "string",
                "enum": ["small", "medium", "large", "all"],
                "description": "Size category (for dogs mainly)"
            },
            "brand": {
                "type": "string",
                "description": "Specific brand if mentioned"
            }
        },
        "required": ["query"]
    }
}


def extract_search_intent(user_query: str) -> Dict:
    """
    Extract search intent and entities from natural language query.

    This is the magic! GPT understands:
    - "salmon-free" → dietary_exclusions: ["salmon"]
    - "grain free" → dietary_exclusions: ["grain"]
    - "without chicken or beef" → dietary_exclusions: ["chicken", "beef"]
    - "hypoallergenic" → dietary_requirements: ["limited-ingredient"]
    - "under $50" → price_max: 50
    - "large breed puppy" → size_category: "large", life_stage: "puppy"

    Args:
        user_query: Natural language search query

    Returns:
        Extracted intent as dictionary
    """
    print(f"\n🧠 NLU: Parsing '{user_query}'...")

    # TODO 1: Call GPT with function calling
    # Hint: Use client.chat.completions.create() with:
    #   - model="gpt-4o-mini"
    #   - messages with system prompt explaining the task
    #   - tools parameter with SEARCH_FUNCTION_SCHEMA
    #   - tool_choice to force function calling

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert at parsing pet product search queries.

Key patterns to recognize:
- "WITH {ingredient}" or "includes {ingredient}" → dietary_requirements (positive - must contain)
- "{ingredient}-free" or "without {ingredient}" → dietary_exclusions (negative - must NOT contain)
- "no chicken and beef" → dietary_exclusions: ["chicken", "beef"]
- "hypoallergenic" → dietary_requirements: ["limited-ingredient"]
- "under $X" or "less than $X" → price_max
- "puppy", "senior", "adult" → life_stage
- "large breed", "small breed" → size_category

IMPORTANT: Distinguish between:
- Positive requirements (WITH X, contains X, includes X) → dietary_requirements
- Negative exclusions (X-free, without X, no X) → dietary_exclusions

Extract ALL relevant information from the query."""
                },
                {
                    "role": "user",
                    "content": f"Parse this search query: {user_query}"
                }
            ],
            tools=[{
                "type": "function",
                "function": SEARCH_FUNCTION_SCHEMA
            }],
            tool_choice={"type": "function", "function": {"name": "search_products"}}
        )

        # TODO 2: Extract function call arguments
        # Hint: response.choices[0].message.tool_calls[0].function.arguments
        tool_call = response.choices[0].message.tool_calls[0]
        intent_data = json.loads(tool_call.function.arguments)

        print(f"   ✓ Extracted: {json.dumps(intent_data, indent=2)}")
        return intent_data

    except Exception as e:
        print(f"   ✗ Error: {e}")
        # Fallback: return basic query
        return {"query": user_query}


def intelligent_search(user_query: str, search_engine):
    """
    End-to-end: NLU + Search

    This combines Phase 2 (search engine) + Phase 3 (NLU)!

    Args:
        user_query: Natural language query
        search_engine: ProductSearch instance

    Returns:
        Search results
    """
    # Step 1: Extract intent with NLU
    intent = extract_search_intent(user_query)

    # Step 2: Call search engine with extracted parameters
    results = search_engine.search(
        query=intent.get("query", user_query),
        dietary_exclusions=intent.get("dietary_exclusions"),
        target_pet=intent.get("target_pet"),
        max_results=5
    )

    return results


def test_nlu():
    """Test the NLU with various queries."""
    print("="*80)
    print("NLU TESTING - Alexa Intent/Slot vs LLM Function Calling")
    print("="*80)

    test_queries = [
        "salmon-free dog food",
        "grain free cat food",
        "dog food without chicken or beef",
        "hypoallergenic food for large breed puppies",
        "organic senior dog food under $60",
        "Blue Buffalo grain-free",
        "limited ingredient food for cats with allergies",
        "high protein puppy food no grain",
    ]

    for query in test_queries:
        intent = extract_search_intent(query)
        print()  # Spacing


if __name__ == "__main__":
    # Test NLU parsing
    test_nlu()

    print("\n" + "="*80)
    print("INTEGRATION TEST - NLU + Search")
    print("="*80)

    # Import search engine
    from product_search import ProductSearch

    # Initialize
    search = ProductSearch()
    search.load_products()

    # Test end-to-end intelligent search
    test_queries = [
        "salmon-free dog food",
        "grain free large breed puppy food under $50",
    ]

    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"USER QUERY: '{query}'")
        print(f"{'='*80}")

        results = intelligent_search(query, search)

        print(f"\nTop Results:")
        for i, result in enumerate(results[:3], 1):
            print(f"\n{i}. {result['name']}")
            print(f"   ${result['price']:.2f} | {result['brand']}")
            print(f"   Similarity: {result['similarity']:.3f}")
