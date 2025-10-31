"""
Product Catalog Generator for Pet Product Chatbot
Generates 100 realistic pet products using OpenAI GPT-4o-mini
"""

import json
import os
from typing import List, Dict
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_products(num_products: int = 100) -> List[Dict]:
    """
    Generate realistic pet product catalog using OpenAI.

    Args:
        num_products: Number of products to generate

    Returns:
        List of product dictionaries
    """
    print(f"Generating {num_products} pet products using GPT-4o-mini...")

    prompt = f"""Generate a JSON array of exactly {num_products} realistic pet products for an e-commerce pet supply store.

Each product should have this exact structure:
{{
    "id": "unique_id_string",
    "name": "Product Name",
    "description": "Detailed 2-3 sentence product description",
    "price": 19.99,
    "target_pet": "dog" or "cat" or "bird" or "fish",
    "ingredients": ["ingredient1", "ingredient2", "ingredient3"],
    "dietary_tags": ["grain-free", "high-protein", etc],
    "brand": "Brand Name",
    "life_stage": "puppy" or "adult" or "senior" or "all",
    "size_category": "small" or "medium" or "large" or "all"
}}

Requirements:
- Mix of dog (40%), cat (40%), bird (10%), fish (10%) products
- Include various product types: dry food, wet food, treats, supplements, toys
- Use real pet food brands (Blue Buffalo, Purina, Hill's Science Diet, Royal Canin, Wellness, etc)
- Dietary tags should include: grain-free, high-protein, limited-ingredient, organic, natural, chicken-free, beef-free, dairy-free, soy-free, etc
- Include products that cater to allergies and dietary restrictions
- Price range: $5-$150
- Realistic ingredients based on actual pet foods
- IDs should be like "prod_001", "prod_002", etc
- Ensure variety in life_stage and size_category

Return ONLY the JSON array, no other text."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a pet product catalog expert. Generate realistic, detailed product data in valid JSON format."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=16000
        )

        # Extract and parse JSON
        content = response.choices[0].message.content.strip()

        # Remove markdown code blocks if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        products = json.loads(content)

        print(f"Successfully generated {len(products)} products!")
        return products

    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        print(f"Response content: {content[:500]}...")
        raise
    except Exception as e:
        print(f"Error generating products: {e}")
        raise


def save_products(products: List[Dict], output_path: str = "data/products.json") -> None:
    """
    Save products to JSON file.

    Args:
        products: List of product dictionaries
        output_path: Path to save JSON file
    """
    # Ensure data directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(products, f, indent=2, ensure_ascii=False)

    print(f"Products saved to {output_path}")


def print_sample_products(products: List[Dict], num_samples: int = 3) -> None:
    """
    Print sample products for verification.

    Args:
        products: List of product dictionaries
        num_samples: Number of samples to print
    """
    print(f"\n{'='*80}")
    print(f"SAMPLE PRODUCTS (showing {num_samples} of {len(products)}):")
    print(f"{'='*80}\n")

    for i, product in enumerate(products[:num_samples], 1):
        print(f"Sample {i}:")
        print(json.dumps(product, indent=2))
        print(f"\n{'-'*80}\n")

    # Print statistics
    pet_types = {}
    for product in products:
        pet = product.get('target_pet', 'unknown')
        pet_types[pet] = pet_types.get(pet, 0) + 1

    print("Product Distribution:")
    for pet, count in sorted(pet_types.items()):
        print(f"  {pet}: {count} products")
    print()


def main():
    """Main execution function."""
    try:
        # Check for API key
        if not os.getenv("OPENAI_API_KEY"):
            print("ERROR: OPENAI_API_KEY not found in environment variables.")
            print("Please create a .env file with your OpenAI API key.")
            print("See .env.example for reference.")
            return

        # Generate products
        products = generate_products(num_products=100)

        # Save to file
        output_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data",
            "products.json"
        )
        save_products(products, output_path)

        # Print samples
        print_sample_products(products, num_samples=2)

        print("Product generation complete!")

    except Exception as e:
        print(f"Error in main: {e}")
        raise


if __name__ == "__main__":
    main()
