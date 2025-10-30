"""
Database Manager for Chewy Pet Chatbot
Handles SQLite database initialization and CRUD operations
"""

import sqlite3
import json
import os
from typing import Optional, List, Dict, Tuple
from datetime import datetime


class DatabaseManager:
    """Manages SQLite database operations for customer, pet, and preference data."""

    def __init__(self, db_path: str = "database/chatbot.db"):
        """
        Initialize database manager.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        """
        Create and return database connection.

        Returns:
            SQLite connection object
        """
        if self.connection is None:
            # Ensure database directory exists
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # Enable column access by name
        return self.connection

    def close(self) -> None:
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None

    def initialize_database(self) -> None:
        """
        Initialize database with schema from schema.sql file.
        Creates tables if they don't exist.
        """
        schema_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "schema.sql"
        )

        conn = self.connect()
        cursor = conn.cursor()

        # Read and execute schema
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
            cursor.executescript(schema_sql)

        conn.commit()
        print(f"Database initialized at {self.db_path}")

    # ==================== Customer Operations ====================

    def create_customer(self, name: str) -> int:
        """
        Create a new customer.

        Args:
            name: Customer name

        Returns:
            Customer ID
        """
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO customers (name) VALUES (?)",
            (name,)
        )
        conn.commit()
        return cursor.lastrowid

    def get_customer(self, customer_id: int) -> Optional[Dict]:
        """
        Get customer by ID.

        Args:
            customer_id: Customer ID

        Returns:
            Customer dictionary or None if not found
        """
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM customers WHERE id = ?",
            (customer_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_customer_by_name(self, name: str) -> Optional[Dict]:
        """
        Get customer by name.

        Args:
            name: Customer name

        Returns:
            Customer dictionary or None if not found
        """
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM customers WHERE name = ?",
            (name,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    # ==================== Pet Operations ====================

    def create_pet(
        self,
        customer_id: int,
        name: str,
        pet_type: str,
        breed: Optional[str] = None,
        allergies: Optional[List[str]] = None
    ) -> int:
        """
        Create a new pet record.

        Args:
            customer_id: Owner customer ID
            name: Pet name
            pet_type: Type of pet (dog, cat, bird, fish, other)
            breed: Pet breed (optional)
            allergies: List of allergies (optional)

        Returns:
            Pet ID
        """
        conn = self.connect()
        cursor = conn.cursor()

        allergies_json = json.dumps(allergies) if allergies else None

        cursor.execute(
            """INSERT INTO pets (customer_id, name, pet_type, breed, allergies_json)
               VALUES (?, ?, ?, ?, ?)""",
            (customer_id, name, pet_type, breed, allergies_json)
        )
        conn.commit()
        return cursor.lastrowid

    def get_pet(self, pet_id: int) -> Optional[Dict]:
        """
        Get pet by ID.

        Args:
            pet_id: Pet ID

        Returns:
            Pet dictionary with allergies parsed from JSON
        """
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pets WHERE id = ?", (pet_id,))
        row = cursor.fetchone()

        if row:
            pet_dict = dict(row)
            # Parse allergies JSON
            if pet_dict.get('allergies_json'):
                pet_dict['allergies'] = json.loads(pet_dict['allergies_json'])
            else:
                pet_dict['allergies'] = []
            return pet_dict
        return None

    def get_customer_pets(self, customer_id: int) -> List[Dict]:
        """
        Get all pets for a customer.

        Args:
            customer_id: Customer ID

        Returns:
            List of pet dictionaries
        """
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM pets WHERE customer_id = ?",
            (customer_id,)
        )
        rows = cursor.fetchall()

        pets = []
        for row in rows:
            pet_dict = dict(row)
            # Parse allergies JSON
            if pet_dict.get('allergies_json'):
                pet_dict['allergies'] = json.loads(pet_dict['allergies_json'])
            else:
                pet_dict['allergies'] = []
            pets.append(pet_dict)

        return pets

    # ==================== Preference Operations ====================

    def set_preference(
        self,
        customer_id: int,
        preference_key: str,
        preference_value: str
    ) -> None:
        """
        Set or update a customer preference.

        Args:
            customer_id: Customer ID
            preference_key: Preference key (e.g., 'dietary_preference', 'budget_max')
            preference_value: Preference value
        """
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute(
            """INSERT INTO preferences (customer_id, preference_key, preference_value)
               VALUES (?, ?, ?)
               ON CONFLICT(customer_id, preference_key)
               DO UPDATE SET preference_value = excluded.preference_value""",
            (customer_id, preference_key, preference_value)
        )
        conn.commit()

    def get_preference(
        self,
        customer_id: int,
        preference_key: str
    ) -> Optional[str]:
        """
        Get a specific customer preference.

        Args:
            customer_id: Customer ID
            preference_key: Preference key

        Returns:
            Preference value or None if not found
        """
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT preference_value FROM preferences
               WHERE customer_id = ? AND preference_key = ?""",
            (customer_id, preference_key)
        )
        row = cursor.fetchone()
        return row['preference_value'] if row else None

    def get_all_preferences(self, customer_id: int) -> Dict[str, str]:
        """
        Get all preferences for a customer.

        Args:
            customer_id: Customer ID

        Returns:
            Dictionary of preference_key: preference_value
        """
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT preference_key, preference_value FROM preferences WHERE customer_id = ?",
            (customer_id,)
        )
        rows = cursor.fetchall()
        return {row['preference_key']: row['preference_value'] for row in rows}

    # ==================== Utility Methods ====================

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def initialize_db(db_path: str = "database/chatbot.db") -> None:
    """
    Convenience function to initialize the database.

    Args:
        db_path: Path to SQLite database file
    """
    db_manager = DatabaseManager(db_path)
    db_manager.initialize_database()
    db_manager.close()


if __name__ == "__main__":
    # Initialize database when run directly
    print("Initializing database...")
    initialize_db()
    print("Database initialization complete!")
