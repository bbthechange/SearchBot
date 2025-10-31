"""
Complete Chatbot - Integrating NLU + Search + Memory

This brings everything together:
- Phase 2: Vector search engine
- Phase 3: LLM-based NLU
- Memory: Conversation context + customer profiles
"""

from typing import Dict
from product_search import ProductSearch
from nlu import extract_search_intent
from memory import ConversationMemory, CustomerMemory


class PetProductChatbot:
    """
    End-to-end chatbot with multi-turn conversation support.
    """

    def __init__(self, customer_email: str = "demo@example.com"):
        """Initialize chatbot with all components."""
        print("🤖 Initializing Pet Product Chatbot...")

        # Initialize components
        self.search_engine = ProductSearch()
        self.conversation = ConversationMemory()
        self.customer_memory = CustomerMemory()

        # Load customer profile
        self.customer_id = self.customer_memory.get_or_create_customer(
            name="Demo Customer",
            email=customer_email
        )

        # Load products into search engine
        print("📦 Loading product catalog...")
        self.search_engine.load_products()

        # Get customer's saved exclusions
        self.saved_exclusions = self.customer_memory.get_dietary_exclusions_for_customer(
            self.customer_id
        )
        if self.saved_exclusions:
            print(f"💾 Loaded customer allergies: {self.saved_exclusions}")

        print("✅ Chatbot ready!\n")

    def chat(self, user_message: str) -> Dict:
        """
        Process a user message and return results.

        This is the main entry point that:
        1. Extracts intent with NLU
        2. Resolves references using conversation memory
        3. Merges with saved customer preferences
        4. Searches products
        5. Updates conversation history
        """
        print(f"\n{'='*80}")
        print(f"USER: {user_message}")
        print(f"{'='*80}")

        # Step 1: Extract intent with NLU
        raw_intent = extract_search_intent(user_message)

        # Step 2: Resolve references using conversation context
        resolved_intent = self.conversation.resolve_reference_query(
            user_message,
            raw_intent
        )

        # Step 3: Merge with saved customer exclusions
        existing_exclusions = resolved_intent.get("dietary_exclusions", [])
        merged_exclusions = list(set(existing_exclusions + self.saved_exclusions))
        if merged_exclusions != existing_exclusions:
            resolved_intent["dietary_exclusions"] = merged_exclusions
            print(f"   💾 Merged with saved allergies: {merged_exclusions}")

        # Step 4: Search products
        results = self.search_engine.search(
            query=resolved_intent.get("query", user_message),
            dietary_exclusions=resolved_intent.get("dietary_exclusions"),
            dietary_requirements=resolved_intent.get("dietary_requirements"),
            target_pet=resolved_intent.get("target_pet"),
            max_results=5
        )

        # Step 5: Update conversation memory
        self.conversation.add_user_message(user_message, resolved_intent)
        self.conversation.add_bot_message(
            f"Found {len(results)} products",
            results
        )

        # Step 6: Check if user mentioned pet allergies (save for next time)
        self._extract_and_save_pet_info(user_message, resolved_intent)

        return {
            "intent": resolved_intent,
            "results": results,
            "context": self.conversation.get_conversation_summary()
        }

    def _extract_and_save_pet_info(self, message: str, intent: Dict):
        """
        Detect if user mentioned pet info and save to long-term memory.

        Examples:
        - "My golden retriever Max is allergic to chicken"
        - "I have a cat named Luna who can't eat grain"
        """
        message_lower = message.lower()

        # Simple pattern detection (in production, use LLM to extract this)
        if "allergic" in message_lower or "can't eat" in message_lower or "cannot eat" in message_lower:
            # Extract pet info
            pet_data = {
                "name": "Pet",  # Would use NER to extract actual name
                "pet_type": intent.get("target_pet", "dog"),
                "breed": None,  # Would extract from message
                "allergies": intent.get("dietary_exclusions", []),
                "life_stage": intent.get("life_stage"),
                "size_category": intent.get("size_category")
            }

            # Save to database
            self.customer_memory.save_pet_profile(self.customer_id, pet_data)

            # Update in-memory cache
            self.saved_exclusions = self.customer_memory.get_dietary_exclusions_for_customer(
                self.customer_id
            )


def demo_multi_turn():
    """
    Demonstrate multi-turn conversation with memory.
    """
    print("="*80)
    print("MULTI-TURN CONVERSATION DEMO")
    print("="*80)

    chatbot = PetProductChatbot()

    # Conversation sequence
    conversation = [
        "salmon-free dog food",
        "show me cheaper options",
        "what about without chicken too?",
        "actually, show me options for cats instead",
    ]

    for message in conversation:
        response = chatbot.chat(message)

        # Display results
        print(f"\n📊 RESULTS ({len(response['results'])} products):")
        for i, product in enumerate(response['results'][:3], 1):
            print(f"  {i}. {product['name']}")
            print(f"     ${product['price']:.2f} | {product['brand']} | Score: {product['similarity']:.3f}")

        print(f"\n📝 Context: {response['context']}")
        print()

    # Test persistence across sessions
    print("\n" + "="*80)
    print("TESTING LONG-TERM MEMORY (New Session)")
    print("="*80)

    # Simulate saving allergy info
    chatbot.chat("My dog is allergic to chicken")

    # Create new chatbot instance (simulates new session)
    print("\n--- New Session (Customer Returns) ---\n")
    chatbot2 = PetProductChatbot()

    # Search should automatically exclude chicken
    response = chatbot2.chat("Find dog food under $50")

    print(f"\n📊 RESULTS (should exclude chicken automatically):")
    for i, product in enumerate(response['results'][:3], 1):
        print(f"  {i}. {product['name']}")
        print(f"     Ingredients: {product.get('ingredients', 'N/A')[:80]}...")


if __name__ == "__main__":
    demo_multi_turn()
