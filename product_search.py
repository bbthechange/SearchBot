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
import numpy as np

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
        # Initialize Chroma client
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")

        # Create/get collection with OpenAI embedding function
        openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.getenv("OPENAI_API_KEY"),
            model_name="text-embedding-3-small"
        )

        self.collection = self.chroma_client.get_or_create_collection(
            name=collection_name,
            embedding_function=openai_ef,
            metadata={"description": "Pet product catalog with semantic search"}
        )

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
            ids.append(product["id"])

            # Create document text (what gets embedded)
            # Example: "Blue Buffalo Life Protection Formula Dog Food. This premium dry dog food..."
            doc_text = f"{product['name']}. {product['description']}"
            documents.append(doc_text)

            # Create metadata dict
            metadata = {
                "product_id": product["id"],
                "name": product["name"],
                "price": product["price"],
                "target_pet": product["target_pet"],
                "brand": product["brand"],
                "life_stage": product.get("life_stage", "all"),
                "size_category": product.get("size_category", "all"),
                "ingredients": ",".join(product.get("ingredients", [])),
                "dietary_tags": ",".join(product.get("dietary_tags", [])),
                # Add boolean flags for common allergens
                "has_salmon": "salmon" in ",".join(product.get("ingredients", [])).lower(),
                "has_chicken": "chicken" in ",".join(product.get("ingredients", [])).lower(),
                "has_grain": any(g in ",".join(product.get("ingredients", [])).lower()
                                for g in ["wheat", "corn", "grain", "barley", "rice"]),
            }
            metadatas.append(metadata)

        # Add to collection
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

        print(f"Successfully loaded {len(products)} products into vector store!")

    def create_contrastive_embedding(
        self,
        query: str,
        exclusions: Optional[List[str]] = None,
        requirements: Optional[List[str]] = None,
        alpha: float = 0.7
    ) -> List[float]:
        """
        Create embedding with contrastive learning for negative/positive intent.

        This uses vector arithmetic to encode intent:
        - Exclusions: Subtract their embeddings (push away from unwanted items)
        - Requirements: Add their embeddings (pull towards wanted items)

        Example:
            "salmon-free dog food" → embed("dog food") - α * embed("salmon")
            Makes query dissimilar to salmon products!

        Args:
            query: Base search query
            exclusions: Terms to push away from (e.g., ["salmon"])
            requirements: Terms to pull towards (e.g., ["grain"])
            alpha: Weight for contrastive terms (0.5-1.0)

        Returns:
            Adjusted embedding as list of floats
        """
        print(f"   🔬 Using contrastive embeddings (α={alpha})")

        # Get base query embedding
        base_response = client.embeddings.create(
            model="text-embedding-3-small",
            input=query
        )
        base_embedding = np.array(base_response.data[0].embedding)

        # Subtract exclusion embeddings (negative contrast)
        if exclusions:
            print(f"   ➖ Subtracting: {exclusions}")
            for exclusion in exclusions:
                excl_response = client.embeddings.create(
                    model="text-embedding-3-small",
                    input=exclusion
                )
                excl_embedding = np.array(excl_response.data[0].embedding)
                base_embedding = base_embedding - alpha * excl_embedding

        # Add requirement embeddings (positive contrast)
        if requirements:
            print(f"   ➕ Adding: {requirements}")
            for requirement in requirements:
                # Boost with related terms
                boost_text = requirement
                if requirement.lower() == "grain":
                    boost_text = "whole grain rice barley oats wheat"

                req_response = client.embeddings.create(
                    model="text-embedding-3-small",
                    input=boost_text
                )
                req_embedding = np.array(req_response.data[0].embedding)
                base_embedding = base_embedding + alpha * req_embedding

        # Normalize (important! keeps vector in unit sphere)
        norm = np.linalg.norm(base_embedding)
        if norm > 0:
            normalized = base_embedding / norm
        else:
            normalized = base_embedding

        return normalized.tolist()

    def search(
        self,
        query: str,
        dietary_exclusions: Optional[List[str]] = None,
        dietary_requirements: Optional[List[str]] = None,
        target_pet: Optional[str] = None,
        max_results: int = 5
    ) -> List[Dict]:
        """
        Search for products using semantic search + metadata filtering.

        This is the CORE function that demonstrates hybrid search!

        Args:
            query: Natural language search query
            dietary_exclusions: Ingredients to EXCLUDE (e.g., ["salmon", "chicken"])
            dietary_requirements: Ingredients that MUST be present (e.g., ["grain"])
            target_pet: Filter by pet type (e.g., "dog", "cat")
            max_results: Number of results to return

        Returns:
            List of matching products with similarity scores
        """
        print(f"\n🔍 Searching for: '{query}'")
        if dietary_exclusions:
            print(f"   Excluding: {dietary_exclusions}")
        if dietary_requirements:
            print(f"   Requiring: {dietary_requirements}")
        if target_pet:
            print(f"   For: {target_pet}")

        # Build metadata filter (WHERE clause)
        where_filter = None
        conditions = []
        if target_pet:
            conditions.append({"target_pet": {"$eq": target_pet}})

        if dietary_exclusions:
            # Use boolean flags
            for exclusion in dietary_exclusions:
                if exclusion.lower() == "salmon":
                    conditions.append({"has_salmon": {"$eq": False}})
                elif exclusion.lower() == "chicken":
                    conditions.append({"has_chicken": {"$eq": False}})
                elif exclusion.lower() in ["grain", "grains"]:
                    conditions.append({"has_grain": {"$eq": False}})

        # Build final filter
        if len(conditions) == 0:
            where_filter = None
        elif len(conditions) == 1:
            where_filter = conditions[0]  # Single condition, no $and needed
        else:
            where_filter = {"$and": conditions}  # Multiple conditions, wrap in $and

        # Query the collection
        # Use contrastive embeddings if we have exclusions/requirements
        if dietary_exclusions or dietary_requirements:
            # Create contrastive embedding (vector arithmetic!)
            query_embedding = self.create_contrastive_embedding(
                query=query,
                exclusions=dietary_exclusions,
                requirements=dietary_requirements
            )
            results = self.collection.query(
                query_embeddings=[query_embedding],  # Use our custom embedding
                where=where_filter,
                n_results=max_results * 3
            )
        else:
            # Standard semantic search
            results = self.collection.query(
                query_texts=[query],  # Let Chroma embed it
                where=where_filter,
                n_results=max_results * 3
            )

        # Format results
        # Chroma returns {ids, documents, metadatas, distances}
        # Transform into list of dicts with product info + similarity score
        formatted_results = []

        if results and results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                metadata = results['metadatas'][0][i]

                # Post-filter for dietary exclusions (safety net)
                if dietary_exclusions:
                    ingredients_str = metadata.get('ingredients', '').lower()
                    # Check if any exclusion is in ingredients
                    if any(exclusion.lower() in ingredients_str for exclusion in dietary_exclusions):
                        continue  # Skip this product

                # Post-filter for dietary requirements (must have ALL)
                if dietary_requirements:
                    ingredients_str = metadata.get('ingredients', '').lower()
                    # For "grain", check for any grain type
                    if 'grain' in [r.lower() for r in dietary_requirements]:
                        has_grain = any(g in ingredients_str for g in ['rice', 'barley', 'wheat', 'oat', 'corn', 'grain'])
                        if not has_grain:
                            continue  # Skip if doesn't have grain
                    else:
                        # For other requirements, check literally
                        if not all(req.lower() in ingredients_str for req in dietary_requirements):
                            continue

                # Calculate similarity score (Chroma returns distance, convert to similarity)
                distance = results['distances'][0][i]
                similarity = 1 - distance  # Closer to 1 = more similar

                formatted_results.append({
                    "id": results['ids'][0][i],
                    "name": metadata.get('name'),
                    "similarity": similarity,
                    "brand": metadata.get('brand'),
                    "price": metadata.get('price'),
                    "target_pet": metadata.get('target_pet'),
                    "ingredients": metadata.get('ingredients'),
                    "dietary_tags": metadata.get('dietary_tags'),
                    "description": results['documents'][0][i]
                })

                # Stop when we have enough results
                if len(formatted_results) >= max_results:
                    break

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
