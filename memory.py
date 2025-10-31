"""
Memory Management - Conversation History & Customer Profiles

Demonstrates two types of memory:
1. Conversation Memory (short-term): Context within a chat session
2. Customer Profile Memory (long-term): Persisted preferences across sessions
"""

import json
import sqlite3
from typing import List, Dict, Optional
from datetime import datetime


class ConversationMemory:
    """
    Short-term memory for a single conversation session.

    Tracks:
    - Recent queries and results
    - Extracted entities (pet type, exclusions, price ranges)
    - Context for resolving references ("it", "cheaper", "that one")
    """

    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.messages: List[Dict] = []
        self.last_query: Optional[Dict] = None
        self.last_results: List[Dict] = []
        self.context: Dict = {
            "current_pet": None,
            "current_exclusions": [],
            "price_range": None,
            "last_brands_shown": []
        }

    def add_user_message(self, message: str, intent: Dict = None):
        """Add user message and update context."""
        self.messages.append({
            "role": "user",
            "content": message,
            "intent": intent,
            "timestamp": datetime.now().isoformat()
        })

        # Update context from intent
        if intent:
            if intent.get("target_pet"):
                self.context["current_pet"] = intent["target_pet"]

            if intent.get("dietary_exclusions"):
                # Accumulate exclusions across conversation
                for excl in intent["dietary_exclusions"]:
                    if excl not in self.context["current_exclusions"]:
                        self.context["current_exclusions"].append(excl)

            if intent.get("price_max"):
                self.context["price_range"] = {
                    "max": intent["price_max"],
                    "min": intent.get("price_min", 0)
                }

            self.last_query = intent

        # Trim old messages
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]

    def add_bot_message(self, message: str, results: List[Dict] = None):
        """Add bot response and update results context."""
        self.messages.append({
            "role": "assistant",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })

        if results:
            self.last_results = results
            # Track brands shown for "show me different brands"
            self.context["last_brands_shown"] = list(set(
                r.get("brand") for r in results if r.get("brand")
            ))

    def resolve_reference_query(self, query: str, intent: Dict) -> Dict:
        """
        Resolve references in follow-up queries.

        Examples:
        - "cheaper options" → inherit context, lower price_max
        - "what about for cats" → change pet, keep exclusions
        - "without chicken too" → add to existing exclusions
        """
        resolved_intent = intent.copy()

        query_lower = query.lower()

        # Detect comparative queries ("cheaper", "more expensive", "larger")
        if "cheaper" in query_lower or "less expensive" in query_lower:
            if self.last_results:
                # Set price_max to average of last results
                avg_price = sum(r.get("price", 0) for r in self.last_results) / len(self.last_results)
                resolved_intent["price_max"] = avg_price * 0.8  # 20% cheaper
                print(f"   💡 Resolved 'cheaper' → price_max: ${resolved_intent['price_max']:.2f}")

        elif "more expensive" in query_lower or "premium" in query_lower:
            if self.last_results:
                avg_price = sum(r.get("price", 0) for r in self.last_results) / len(self.last_results)
                resolved_intent["price_min"] = avg_price * 1.2
                print(f"   💡 Resolved 'more expensive' → price_min: ${resolved_intent['price_min']:.2f}")

        # Inherit context if not specified
        if not resolved_intent.get("target_pet") and self.context["current_pet"]:
            resolved_intent["target_pet"] = self.context["current_pet"]
            print(f"   💡 Inherited pet type: {resolved_intent['target_pet']}")

        # Accumulate exclusions if using "also", "too", "additionally"
        if any(word in query_lower for word in ["also", "too", "additionally", "and"]):
            existing = self.context.get("current_exclusions", [])
            new_exclusions = resolved_intent.get("dietary_exclusions", [])
            resolved_intent["dietary_exclusions"] = list(set(existing + new_exclusions))
            if existing and new_exclusions:
                print(f"   💡 Accumulated exclusions: {resolved_intent['dietary_exclusions']}")

        # Handle "different brands"
        if "different" in query_lower and "brand" in query_lower:
            resolved_intent["exclude_brands"] = self.context.get("last_brands_shown", [])
            print(f"   💡 Excluding brands: {resolved_intent['exclude_brands']}")

        return resolved_intent

    def get_conversation_summary(self) -> str:
        """Get a summary of the conversation for context."""
        summary = []
        if self.context["current_pet"]:
            summary.append(f"Shopping for: {self.context['current_pet']}")
        if self.context["current_exclusions"]:
            summary.append(f"Excluding: {', '.join(self.context['current_exclusions'])}")
        if self.context["price_range"]:
            pr = self.context["price_range"]
            summary.append(f"Price range: ${pr['min']}-${pr['max']}")

        return " | ".join(summary) if summary else "No active filters"


class CustomerMemory:
    """
    Long-term memory persisted to SQLite.

    Stores:
    - Customer profiles
    - Pet information (name, type, breed, allergies)
    - Shopping preferences
    """

    def __init__(self, db_path: str = "customer_memory.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Customers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                email TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Pets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                name TEXT,
                pet_type TEXT,
                breed TEXT,
                allergies TEXT,  -- JSON array of allergens
                life_stage TEXT,
                size_category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            )
        """)

        # Preferences table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                preference_key TEXT,
                preference_value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            )
        """)

        conn.commit()
        conn.close()

    def get_or_create_customer(self, name: str = "Demo Customer", email: str = "demo@example.com") -> int:
        """Get or create a customer profile."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM customers WHERE email = ?", (email,))
        row = cursor.fetchone()

        if row:
            customer_id = row[0]
        else:
            cursor.execute("INSERT INTO customers (name, email) VALUES (?, ?)", (name, email))
            customer_id = cursor.lastrowid
            conn.commit()

        conn.close()
        return customer_id

    def save_pet_profile(self, customer_id: int, pet_data: Dict):
        """Save or update pet information."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO pets (customer_id, name, pet_type, breed, allergies, life_stage, size_category)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            customer_id,
            pet_data.get("name"),
            pet_data.get("pet_type"),
            pet_data.get("breed"),
            json.dumps(pet_data.get("allergies", [])),
            pet_data.get("life_stage"),
            pet_data.get("size_category")
        ))

        conn.commit()
        conn.close()

        print(f"   💾 Saved pet profile: {pet_data.get('name')} ({pet_data.get('pet_type')})")

    def get_customer_pets(self, customer_id: int) -> List[Dict]:
        """Retrieve all pets for a customer."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT name, pet_type, breed, allergies, life_stage, size_category
            FROM pets
            WHERE customer_id = ?
        """, (customer_id,))

        pets = []
        for row in cursor.fetchall():
            pets.append({
                "name": row[0],
                "pet_type": row[1],
                "breed": row[2],
                "allergies": json.loads(row[3]) if row[3] else [],
                "life_stage": row[4],
                "size_category": row[5]
            })

        conn.close()
        return pets

    def get_dietary_exclusions_for_customer(self, customer_id: int) -> List[str]:
        """Get all dietary exclusions based on customer's pets' allergies."""
        pets = self.get_customer_pets(customer_id)
        all_exclusions = []

        for pet in pets:
            all_exclusions.extend(pet.get("allergies", []))

        return list(set(all_exclusions))  # Remove duplicates


def test_memory():
    """Test memory management."""
    print("="*80)
    print("MEMORY MANAGEMENT TEST")
    print("="*80)

    # Test conversation memory
    print("\n1. CONVERSATION MEMORY (Short-term)")
    print("-" * 80)

    conv = ConversationMemory()

    # Turn 1
    conv.add_user_message(
        "salmon-free dog food",
        intent={"target_pet": "dog", "dietary_exclusions": ["salmon"]}
    )
    print(f"Turn 1: {conv.get_conversation_summary()}")

    # Turn 2 - follow-up
    conv.add_user_message(
        "cheaper options",
        intent={"query": "cheaper"}
    )
    resolved = conv.resolve_reference_query("cheaper options", {"query": "cheaper"})
    print(f"Turn 2 resolved: {resolved}")

    # Turn 3 - add exclusion
    conv.add_user_message(
        "without chicken too",
        intent={"dietary_exclusions": ["chicken"]}
    )
    resolved = conv.resolve_reference_query("without chicken too", {"dietary_exclusions": ["chicken"]})
    print(f"Turn 3 resolved: {resolved}")
    print(f"Context: {conv.get_conversation_summary()}")

    # Test customer memory
    print("\n2. CUSTOMER MEMORY (Long-term)")
    print("-" * 80)

    customer_mem = CustomerMemory()

    # Create customer
    customer_id = customer_mem.get_or_create_customer("Brian Butler", "brian@example.com")
    print(f"Customer ID: {customer_id}")

    # Save pet profile
    customer_mem.save_pet_profile(customer_id, {
        "name": "Max",
        "pet_type": "dog",
        "breed": "Golden Retriever",
        "allergies": ["chicken", "salmon"],
        "life_stage": "adult",
        "size_category": "large"
    })

    # Retrieve
    pets = customer_mem.get_customer_pets(customer_id)
    print(f"Retrieved pets: {pets}")

    exclusions = customer_mem.get_dietary_exclusions_for_customer(customer_id)
    print(f"Dietary exclusions for customer: {exclusions}")


if __name__ == "__main__":
    test_memory()
