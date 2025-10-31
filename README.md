# Pet Product Chatbot with Vector Search

An intelligent conversational AI assistant for pet product recommendations using semantic search, natural language understanding, and customer memory.

## Overview

This chatbot prototype demonstrates modern AI/ML techniques for e-commerce search:
- **Vector Search**: Semantic similarity using embeddings to understand query intent
- **NLU**: GPT-based intent extraction and entity recognition
- **Multi-turn Conversations**: Context-aware dialogue with reference resolution
- **Customer Memory**: Persistent profiles for personalized recommendations

The system supports multiple pet types (dogs, cats, birds, fish) and handles complex requirements like dietary restrictions, allergies, budget constraints, and negative intent ("salmon-free", "grain-free").

## Key Features

### 1. Semantic Search with Negative Intent
- Understands "salmon-free" means exclude salmon (not search for salmon)
- Handles synonyms: "hypoallergenic" → "limited-ingredient"
- Combines vector similarity with metadata filtering

### 2. Natural Language Understanding
- Zero-shot intent extraction using GPT function calling
- Extracts entities: pet type, dietary restrictions, price ranges, brands
- No training data required - works out of the box

### 3. Multi-Turn Context
- Resolves references: "cheaper options" calculates from last results
- Accumulates filters: "also without chicken" adds to existing exclusions
- Inherits context across conversation turns

### 4. Customer Profiles
- Persists pet information and allergies across sessions
- Automatically applies saved preferences
- Supports multiple pets per customer

## Tech Stack

- **Frontend**: Streamlit chat interface with debug panels
- **Vector DB**: ChromaDB for semantic product search
- **LLM**: OpenAI GPT-4o-mini for NLU and data generation
- **Embeddings**: OpenAI text-embedding-3-small (1536 dimensions)
- **Database**: SQLite for customer profiles and preferences
- **Memory**: Conversation state with Redis-ready architecture

## Setup

### Prerequisites

- Python 3.10+
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd chatSearch
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

5. **Generate product catalog**
   ```bash
   python scripts/generate_products.py
   ```
   This creates 100 realistic pet products with ingredients, dietary tags, and prices.

### Running the Application

**Option 1: Command-line demos**
```bash
# Test vector search
python product_search.py

# Test NLU intent extraction
python nlu.py

# Test complete chatbot with multi-turn
python chatbot.py

# Test memory systems
python memory.py
```

**Option 2: Streamlit UI**
```bash
streamlit run app.py
```
Opens at `http://localhost:8501`

## Project Structure

```
chatSearch/
├── app.py                      # Streamlit chat interface
├── product_search.py           # Vector search implementation
├── nlu.py                      # NLU with GPT function calling
├── chatbot.py                  # Complete chatbot integration
├── memory.py                   # Conversation & customer memory
├── requirements.txt            # Python dependencies
├── .env.example                # Environment template
│
├── data/
│   └── products.json           # Generated product catalog
│
├── database/
│   ├── schema.sql              # Database schema
│   ├── db_manager.py           # CRUD operations
│   └── customer_memory.db      # SQLite database (created at runtime)
│
├── scripts/
│   └── generate_products.py   # Synthetic data generator
│
├── vector_store/
│   └── chroma_manager.py       # ChromaDB utilities
│
└── chroma_db/                  # Chroma persistence (created at runtime)
```

## Example Queries

The chatbot understands complex natural language:

```
User: "salmon-free dog food"
→ Excludes products with salmon in ingredients

User: "cheaper options"
→ Calculates price_max from previous results

User: "also without chicken"
→ Adds chicken to existing exclusions

User: "what about for cats instead?"
→ Switches pet type, keeps other filters

User: "My golden retriever is allergic to chicken"
→ Saves to database, auto-applies in future sessions
```

## Architecture Highlights

### Vector Search Pipeline
```
Query: "salmon-free dog food"
  ↓
[1. NLU] Extract intent: {pet: "dog", exclusions: ["salmon"]}
  ↓
[2. Embed] Convert query to 1536-dim vector
  ↓
[3. Search] ChromaDB similarity + metadata filtering
  ↓
[4. Rank] Return top-k products
```

### Memory Architecture
- **Short-term**: Conversation context (Redis-ready, currently in-memory)
- **Long-term**: Customer profiles (SQLite, production: PostgreSQL)
- **Hybrid**: Merges saved preferences with current query

### NLU vs Traditional Search
| Traditional Keyword Search | Vector Search + NLU |
|---------------------------|---------------------|
| "salmon-free" finds "salmon" ❌ | Understands exclusion ✅ |
| "grain free" ≠ "grain-free" ❌ | Same semantic meaning ✅ |
| Can't understand synonyms ❌ | "hypoallergenic" → results ✅ |

## Production Considerations

This is a prototype demonstrating core concepts. For production:

**Scalability:**
- Migrate ChromaDB → Pinecone/Weaviate (millions of products)
- Redis for session storage (distributed state)
- PostgreSQL for customer profiles (ACID compliance)

**Cost Optimization:**
- Self-host embedding model (sentence-transformers)
- Cache common query embeddings (Redis)
- Fine-tune smaller model for NLU (distillation from GPT)

**Reliability:**
- Implement retry logic and fallbacks
- Monitor embedding quality and search relevance
- A/B test retrieval strategies

**Security:**
- Input validation and sanitization
- Rate limiting on API calls
- PII handling for customer data

## Development

### Database Schema

**customers**: id, name, email, created_at

**pets**: id, customer_id, name, pet_type, breed, allergies (JSON), life_stage, size_category

**preferences**: id, customer_id, preference_key, preference_value

### Product Schema
```json
{
  "id": "prod_001",
  "name": "Blue Buffalo Life Protection Formula",
  "description": "Premium dog food with real meat...",
  "price": 49.99,
  "target_pet": "dog",
  "ingredients": ["chicken", "brown rice", "barley"],
  "dietary_tags": ["natural", "high-protein"],
  "brand": "Blue Buffalo",
  "life_stage": "adult",
  "size_category": "medium"
}
```

## Key Concepts Demonstrated

1. **Embeddings**: Text → semantic vectors for similarity search
2. **Hybrid Search**: Vector similarity + structured metadata filtering
3. **Function Calling**: LLM structured output for intent extraction
4. **Context Resolution**: "cheaper" calculates from conversation state
5. **Memory Layers**: Short-term (session) + long-term (persistent)

## Cost Estimates

Prototype usage:
- Embedding 100 products: $0.0002
- Per query: ~$0.00012 (NLU + embedding)
- 1000 queries: ~$0.12

Production optimization can reduce to $0.00001/query with caching and self-hosted models.

## Troubleshooting

**OpenAI API Key Error**
- Verify `.env` file exists and contains valid key
- Restart application after adding key

**Module Not Found**
- Activate virtual environment: `source venv/bin/activate`
- Reinstall: `pip install -r requirements.txt`

**Port Already in Use**
```bash
streamlit run app.py --server.port 8502
```

## License

MIT License - feel free to use for learning and experimentation.

## Acknowledgments

Built with:
- [OpenAI](https://openai.com) for embeddings and LLM
- [ChromaDB](https://www.trychroma.com/) for vector storage
- [LangChain](https://python.langchain.com/) for LLM orchestration
- [Streamlit](https://streamlit.io/) for UI

---

**Note**: This is a demonstration prototype showcasing AI/ML techniques for semantic search and NLU. Not intended for production use without additional hardening, testing, and optimization.
