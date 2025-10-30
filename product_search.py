"""
Product Search Module - Vector Search Implementation
This is where you'll implement semantic search with negative intent handling.
"""

import json
import os
from typing import List, Dict, Optional
from openai import OpenAI
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class ProductSearch:
    """
    Semantic product search using vector embeddings and metadata filtering.

    This class demonstrates how to:
    1. Convert text to embeddings (semantic vectors)
    2. Store products in a vector database
    3. Handle negative intent ("salmon-free") using metadata filters
    """

    def __init__(self, collection_name: str = "pet_products"):
        """
        Initialize the search system.

        Args:
            collection_name: Name of the Chroma collection to use
        """
        # TODO 1: Initialize Chroma client
        # Hint: Use chromadb.Client() for in-memory, or PersistentClient() for disk storage
        self.chroma_client = None  # REPLACE THIS

        # TODO 2: Create/get collection with OpenAI embedding function
        # Hint: Use chroma_client.get_or_create_collection()
        # Hint: Use embedding_functions.OpenAIEmbeddingFunction()
        self.collection = None  # REPLACE THIS

        print(f"Initialized ProductSearch with collection: {collection_name}")

    def load_products(self, products_file: str = "data/products.json") -> None:
        """
        Load products from JSON and add them to the vector store.

        This is where we convert product descriptions to embeddings!

        Args:
            products_file: Path to products JSON file
        """
        print(f"Loading products from {products_file}...")

        # Load products from JSON
        with open(products_file, 'r') as f:
            products = json.load(f)

        print(f"Found {len(products)} products. Creating embeddings...")

        # TODO 3: Prepare data for Chroma
        # We need:
        # - ids: List of product IDs
        # - documents: List of text to embed (name + description)
        # - metadatas: List of metadata dicts (ingredients, price, etc)

        ids = []
        documents = []
        metadatas = []

        for product in products:
            # TODO 3a: Add product ID
            ids.append(product["id"])

            # TODO 3b: Create document text (what gets embedded)
            # Hint: Combine name + description for rich semantic content
            # Example: "Blue Buffalo Life Protection Formula Dog Food. This premium dry dog food..."
            doc_text = "REPLACE THIS"  # YOUR CODE HERE
            documents.append(doc_text)

            # TODO 3c: Create metadata dict
            # Hint: Include ingredients, dietary_tags, price, target_pet, brand, etc
            # Hint: Convert lists to comma-separated strings for Chroma compatibility
            metadata = {
                # YOUR CODE HERE
                # Example: "ingredients": ",".join(product["ingredients"])
            }
            metadatas.append(metadata)

        # TODO 4: Add to collection
        # Hint: Use self.collection.add(ids=..., documents=..., metadatas=...)
        # YOUR CODE HERE

        print(f"Successfully loaded {len(products)} products into vector store!")

    def search(
        self,
        query: str,
        dietary_exclusions: Optional[List[str]] = None,
        target_pet: Optional[str] = None,
        max_results: int = 5
    ) -> List[Dict]:
        """
        Search for products using semantic search + metadata filtering.

        This is the CORE function that demonstrates hybrid search!

        Args:
            query: Natural language search query
            dietary_exclusions: Ingredients to EXCLUDE (e.g., ["salmon", "chicken"])
            target_pet: Filter by pet type (e.g., "dog", "cat")
            max_results: Number of results to return

        Returns:
            List of matching products with similarity scores
        """
        print(f"\n🔍 Searching for: '{query}'")
        if dietary_exclusions:
            print(f"   Excluding: {dietary_exclusions}")
        if target_pet:
            print(f"   For: {target_pet}")

        # TODO 5: Build metadata filter (WHERE clause)
        # This is how we handle NEGATIVE INTENT!
        # Hint: Chroma uses {"field": {"$operator": value}} syntax
        # Hint: For exclusions, we need to ensure ingredients DON'T contain excluded items

        where_filter = None
        if dietary_exclusions or target_pet:
            where_filter = {}
            # YOUR CODE HERE
            # Example for target_pet: {"target_pet": {"$eq": target_pet}}
            # Example for exclusions: Need to check if ingredients contain excluded items
            # Note: This is tricky! You may need to rethink data structure

        # TODO 6: Query the collection
        # Hint: Use self.collection.query(
        #           query_texts=[query],
        #           where=where_filter,
        #           n_results=max_results
        #       )
        results = None  # YOUR CODE HERE

        # TODO 7: Format results
        # Hint: Chroma returns {ids, documents, metadatas, distances}
        # Transform into list of dicts with product info + similarity score
        formatted_results = []
        # YOUR CODE HERE

        return formatted_results

    def explain_results(self, query: str, results: List[Dict]) -> None:
        """
        Print detailed explanation of why products matched.

        This helps you understand HOW vector search works!
        """
        print(f"\n{'='*80}")
        print(f"SEARCH EXPLANATION: '{query}'")
        print(f"{'='*80}\n")

        for i, result in enumerate(results, 1):
            print(f"Result #{i}: {result.get('name', 'Unknown')}")
            print(f"  Similarity Score: {result.get('similarity', 0):.4f}")
            print(f"  Brand: {result.get('brand', 'Unknown')}")
            print(f"  Price: ${result.get('price', 0):.2f}")
            print(f"  Target Pet: {result.get('target_pet', 'Unknown')}")

            ingredients = result.get('ingredients', 'Unknown')
            if isinstance(ingredients, str):
                ingredients = ingredients.split(',')
            print(f"  Ingredients: {', '.join(ingredients[:5])}{'...' if len(ingredients) > 5 else ''}")

            dietary_tags = result.get('dietary_tags', [])
            if dietary_tags:
                print(f"  Dietary Tags: {', '.join(dietary_tags)}")

            print()


def main():
    """
    Test the product search implementation.
    """
    print("="*80)
    print("PRODUCT SEARCH DEMO")
    print("="*80)

    # Initialize search
    search = ProductSearch()

    # Load products
    search.load_products()

    # Test 1: Basic semantic search
    print("\n" + "="*80)
    print("TEST 1: Basic Semantic Search")
    print("="*80)
    results = search.search("salmon dog food")
    search.explain_results("salmon dog food", results)

    # Test 2: Negative intent (THE KEY TEST!)
    print("\n" + "="*80)
    print("TEST 2: Negative Intent - Salmon-Free")
    print("="*80)
    results = search.search(
        "salmon-free dog food",
        dietary_exclusions=["salmon"]
    )
    search.explain_results("salmon-free dog food", results)

    # Test 3: Synonym understanding
    print("\n" + "="*80)
    print("TEST 3: Synonym Understanding")
    print("="*80)
    results = search.search("hypoallergenic cat food")
    search.explain_results("hypoallergenic cat food", results)

    # Test 4: Complex multi-constraint
    print("\n" + "="*80)
    print("TEST 4: Complex Multi-Constraint")
    print("="*80)
    results = search.search(
        "large breed dog food",
        dietary_exclusions=["grain", "chicken", "corn"],
        target_pet="dog"
    )
    search.explain_results("large breed dog food", results)


if __name__ == "__main__":
    main()
