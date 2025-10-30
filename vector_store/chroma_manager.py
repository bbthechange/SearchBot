"""
Chroma Vector Store Manager for Chewy Pet Chatbot
Manages vector embeddings for product search and retrieval
"""

import os
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions


class ChromaManager:
    """Manages Chroma vector store for product embeddings."""

    def __init__(
        self,
        collection_name: str = "pet_products",
        persist_directory: str = "vector_store/chroma_data"
    ):
        """
        Initialize Chroma manager.

        Args:
            collection_name: Name of the Chroma collection
            persist_directory: Directory to persist vector data
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory

        # Ensure persist directory exists
        os.makedirs(persist_directory, exist_ok=True)

        # Initialize Chroma client
        self.client = chromadb.Client(
            Settings(
                persist_directory=persist_directory,
                anonymized_telemetry=False
            )
        )

        # Collection will be initialized when needed
        self.collection = None

    def initialize_collection(
        self,
        embedding_function: Optional[embedding_functions.EmbeddingFunction] = None
    ) -> None:
        """
        Initialize or get the Chroma collection.

        Args:
            embedding_function: Custom embedding function (optional)
                               If None, uses default sentence transformers
        """
        # Use default embedding function if not provided
        if embedding_function is None:
            # Default to sentence transformers (all-MiniLM-L6-v2)
            embedding_function = embedding_functions.DefaultEmbeddingFunction()

        # Get or create collection
        try:
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=embedding_function,
                metadata={"description": "Pet product embeddings for semantic search"}
            )
            print(f"Collection '{self.collection_name}' initialized")
        except Exception as e:
            print(f"Error initializing collection: {e}")
            raise

    def add_products(self, products: List[Dict]) -> None:
        """
        Add products to the vector store.

        TODO: Implement this in Phase 2
        - Create meaningful text representations of products
        - Generate embeddings using OpenAI or sentence transformers
        - Store in Chroma with metadata for filtering

        Args:
            products: List of product dictionaries
        """
        if self.collection is None:
            raise ValueError("Collection not initialized. Call initialize_collection() first.")

        # TODO: Implement product ingestion
        # Example structure:
        # for product in products:
        #     text = self._create_product_text(product)
        #     metadata = self._extract_product_metadata(product)
        #     self.collection.add(
        #         documents=[text],
        #         metadatas=[metadata],
        #         ids=[product['id']]
        #     )

        print(f"TODO: Add {len(products)} products to vector store")

    def search_products(
        self,
        query: str,
        n_results: int = 5,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Search for products using semantic similarity.

        TODO: Implement this in Phase 2
        - Support natural language queries
        - Apply metadata filters (pet type, price range, dietary tags)
        - Return ranked results with similarity scores

        Args:
            query: Natural language search query
            n_results: Number of results to return
            filters: Optional metadata filters (e.g., {"target_pet": "dog"})

        Returns:
            List of product dictionaries with similarity scores
        """
        if self.collection is None:
            raise ValueError("Collection not initialized. Call initialize_collection() first.")

        # TODO: Implement semantic search
        # Example structure:
        # results = self.collection.query(
        #     query_texts=[query],
        #     n_results=n_results,
        #     where=filters
        # )
        # return self._format_search_results(results)

        print(f"TODO: Search for '{query}' with filters {filters}")
        return []

    def _create_product_text(self, product: Dict) -> str:
        """
        Create searchable text representation of a product.

        TODO: Implement this in Phase 2
        - Combine relevant fields (name, description, ingredients, tags)
        - Format for optimal embedding quality

        Args:
            product: Product dictionary

        Returns:
            Text representation
        """
        # Placeholder
        return f"{product.get('name', '')} {product.get('description', '')}"

    def _extract_product_metadata(self, product: Dict) -> Dict:
        """
        Extract metadata for filtering and retrieval.

        TODO: Implement this in Phase 2
        - Extract filterable fields
        - Convert to Chroma-compatible metadata format

        Args:
            product: Product dictionary

        Returns:
            Metadata dictionary
        """
        # Placeholder
        return {
            "target_pet": product.get("target_pet", ""),
            "price": product.get("price", 0),
            "brand": product.get("brand", "")
        }

    def delete_collection(self) -> None:
        """Delete the entire collection (useful for testing/reset)."""
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = None
            print(f"Collection '{self.collection_name}' deleted")
        except Exception as e:
            print(f"Error deleting collection: {e}")

    def get_collection_stats(self) -> Dict:
        """
        Get statistics about the collection.

        Returns:
            Dictionary with collection stats
        """
        if self.collection is None:
            return {"error": "Collection not initialized"}

        try:
            count = self.collection.count()
            return {
                "collection_name": self.collection_name,
                "total_documents": count,
                "persist_directory": self.persist_directory
            }
        except Exception as e:
            return {"error": str(e)}


def initialize_vector_store(products_path: str = "data/products.json") -> None:
    """
    Convenience function to initialize vector store with products.

    TODO: Implement this in Phase 2 once product ingestion is ready

    Args:
        products_path: Path to products JSON file
    """
    import json

    # Load products
    with open(products_path, 'r') as f:
        products = json.load(f)

    # Initialize Chroma
    chroma = ChromaManager()
    chroma.initialize_collection()

    # Add products
    chroma.add_products(products)

    # Print stats
    stats = chroma.get_collection_stats()
    print(f"Vector store initialized: {stats}")


if __name__ == "__main__":
    # Test initialization
    print("Testing Chroma initialization...")
    chroma = ChromaManager()
    chroma.initialize_collection()
    stats = chroma.get_collection_stats()
    print(f"Collection stats: {stats}")
