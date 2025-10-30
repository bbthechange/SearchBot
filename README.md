# Chewy Pet Product Chatbot - Phase 1

A conversational AI assistant for pet product recommendations using vector search and natural language understanding.

## Project Overview

This chatbot prototype helps customers find the perfect pet products by understanding natural language queries and searching through a product catalog using semantic similarity. The system supports multiple pet types (dogs, cats, birds, fish) and handles complex requirements like dietary restrictions, allergies, and budget constraints.

### Architecture

- **Frontend**: Streamlit chat interface with debug mode
- **Vector Store**: ChromaDB for semantic product search
- **Database**: SQLite for customer/pet profiles and preferences
- **LLM**: OpenAI GPT-4o-mini for product generation and (later) intent classification
- **Embeddings**: OpenAI embeddings for vector search

### Project Status

**Phase 1 (Current)**: Complete scaffolding with UI, database, and product data
- Product catalog generation
- Database schema and CRUD operations
- Streamlit chat interface shell
- ChromaDB setup (placeholder functions)

**Phase 2 (Next)**: Implement vector search and NLU components
- Product embedding and ingestion
- Intent classification
- Entity extraction
- Semantic search with filtering

## Setup Instructions

### Prerequisites

- Python 3.9 or higher
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Installation

1. **Clone or navigate to the project directory**
   ```bash
   cd /path/to/chatSearch
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**

   On macOS/Linux:
   ```bash
   source venv/bin/activate
   ```

   On Windows:
   ```bash
   venv\Scripts\activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_actual_api_key_here
   ```

### Generate Product Catalog

Generate 100 realistic pet products using OpenAI:

```bash
python scripts/generate_products.py
```

This will create `data/products.json` with the product catalog. The script will display:
- Progress information
- Sample products
- Distribution statistics (dog/cat/bird/fish)

### Initialize Database

Initialize the SQLite database with schema:

```bash
python database/db_manager.py
```

This creates `database/chatbot.db` with tables for customers, pets, and preferences.

### Run the Application

Launch the Streamlit chat interface:

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## Project Structure

```
chatSearch/
├── app.py                          # Streamlit chat interface
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variables template
├── .env                           # Your environment variables (not in git)
├── .gitignore                     # Git ignore rules
├── README.md                      # This file
│
├── data/
│   └── products.json              # Generated product catalog (100 items)
│
├── database/
│   ├── schema.sql                 # SQLite database schema
│   ├── db_manager.py              # Database CRUD operations
│   └── chatbot.db                 # SQLite database file (created after init)
│
├── scripts/
│   └── generate_products.py       # Product catalog generator
│
└── vector_store/
    ├── chroma_manager.py          # ChromaDB vector store manager
    └── chroma_data/               # Chroma persistence directory (created at runtime)
```

## Usage

### Basic Chat Interface

1. Launch the app with `streamlit run app.py`
2. Type messages in the chat input
3. The bot will respond (Phase 1: placeholder responses)

### Debug Mode

- Toggle "Debug Mode" in the sidebar to see:
  - Intent classification (Phase 2)
  - Entity extraction (Phase 2)
  - Vector search results (Phase 2)
  - Context used for personalization (Phase 2)

### Customer Context

The sidebar shows customer profile information including:
- Customer ID
- Registered pets
- Saved preferences

## Database Schema

### Customers Table
- `id`: Primary key
- `name`: Customer name
- `created_at`: Timestamp

### Pets Table
- `id`: Primary key
- `customer_id`: Foreign key to customers
- `name`: Pet name
- `pet_type`: dog, cat, bird, fish, or other
- `breed`: Breed information
- `allergies_json`: JSON array of allergies
- `created_at`: Timestamp

### Preferences Table
- `id`: Primary key
- `customer_id`: Foreign key to customers
- `preference_key`: Preference name (e.g., "budget_max", "dietary_preference")
- `preference_value`: Preference value
- `created_at`: Timestamp

## Product Data Structure

Each product in `data/products.json` has:

```json
{
  "id": "prod_001",
  "name": "Product Name",
  "description": "Detailed product description",
  "price": 29.99,
  "target_pet": "dog",
  "ingredients": ["chicken", "rice", "vegetables"],
  "dietary_tags": ["grain-free", "high-protein"],
  "brand": "Brand Name",
  "life_stage": "adult",
  "size_category": "medium"
}
```

## Next Steps (Phase 2)

### Vector Search Implementation
1. Implement `add_products()` in `chroma_manager.py`
   - Create product text representations
   - Generate embeddings using OpenAI
   - Ingest into ChromaDB with metadata

2. Implement `search_products()` in `chroma_manager.py`
   - Support natural language queries
   - Apply metadata filters
   - Return ranked results with scores

### NLU Components
1. Intent Classification
   - Detect user intent: search, filter, question, etc.
   - Use OpenAI or fine-tuned model

2. Entity Extraction
   - Extract: pet type, dietary tags, price range, brand, etc.
   - Use structured output from LLM

3. Context Management
   - Track conversation history
   - Maintain user preferences
   - Handle multi-turn dialogues

### Chatbot Logic
1. Implement `process_user_message()` in `app.py`
   - Integrate intent classification
   - Call vector search with filters
   - Generate contextual responses

2. Implement `get_debug_info()` in `app.py`
   - Show intent/entities
   - Display retrieved products
   - Explain reasoning

## Development Notes

- All code uses type hints and docstrings
- TODOs are marked for Phase 2 implementation
- The Streamlit app is fully functional (with placeholder responses)
- Database operations use context managers for safety
- ChromaDB is configured to persist data locally

## Dependencies

- `langchain==0.1.0` - LLM application framework
- `langchain-openai==0.0.5` - OpenAI integration for LangChain
- `chromadb==0.4.22` - Vector database for embeddings
- `streamlit==1.31.0` - Web UI framework
- `openai==1.12.0` - OpenAI API client
- `python-dotenv==1.0.0` - Environment variable management
- `sqlalchemy==2.0.25` - SQL toolkit (future use)

## Troubleshooting

### OpenAI API Key Error
If you see "OPENAI_API_KEY not found":
1. Ensure `.env` file exists in project root
2. Verify the API key is correctly set in `.env`
3. Restart the terminal/application after adding the key

### Module Import Errors
If you see "No module named X":
1. Ensure virtual environment is activated
2. Run `pip install -r requirements.txt`
3. Check Python version (3.9+)

### Streamlit Port Already in Use
If port 8501 is busy:
```bash
streamlit run app.py --server.port 8502
```

## License

This is a prototype project for demonstration purposes.

## Contact

For questions or issues, please refer to the project documentation or create an issue in the repository.
