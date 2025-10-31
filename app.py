"""
Pet Product Chatbot - Streamlit Application
A conversational interface for pet product recommendations using vector search and NLU
"""

import streamlit as st
import os
from typing import Dict, List

# Import our chatbot components
from chatbot import PetProductChatbot

# ==================== Page Configuration ====================

st.set_page_config(
    page_title="Pet Product Chatbot",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== Custom CSS ====================

st.markdown("""
<style>
    .product-card {
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin-bottom: 0.5rem;
        background-color: #f9f9f9;
    }
    .product-name {
        font-weight: bold;
        font-size: 1.1rem;
        color: #1f77b4;
    }
    .product-price {
        color: #2ca02c;
        font-weight: bold;
        font-size: 1.2rem;
    }
    .similarity-score {
        color: #ff7f0e;
        font-size: 0.9rem;
    }
    .debug-section {
        background-color: #f0f0f0;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ==================== Session State Initialization ====================

def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if "chatbot" not in st.session_state:
        with st.spinner("🤖 Initializing chatbot..."):
            st.session_state.chatbot = PetProductChatbot()

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hi! 👋 I'm your pet product assistant. I can help you find products using natural language search!\n\nTry asking:\n- \"salmon-free dog food\"\n- \"grain free cat food under $50\"\n- \"hypoallergenic food for large breed puppies\""
            }
        ]

    if "debug_mode" not in st.session_state:
        st.session_state.debug_mode = False

    if "last_response" not in st.session_state:
        st.session_state.last_response = None

# ==================== Sidebar ====================

def render_sidebar():
    """Render the sidebar with debug controls and information."""
    with st.sidebar:
        st.title("🐾 Pet Product Chatbot")
        st.markdown("**Vector Search + NLU Demo**")
        st.markdown("---")

        # Debug Mode Toggle
        st.subheader("⚙️ Settings")
        debug_mode = st.toggle(
            "Debug Mode",
            value=st.session_state.debug_mode,
            help="Show intent detection, entity extraction, and retrieval details"
        )
        st.session_state.debug_mode = debug_mode

        st.markdown("---")

        # Conversation Context Display
        st.subheader("💭 Conversation Context")
        if st.session_state.chatbot:
            context = st.session_state.chatbot.conversation.get_conversation_summary()
            if context and context != "No active filters":
                st.info(context)
            else:
                st.caption("_No active filters_")

        # Customer Memory Display
        st.subheader("💾 Saved Preferences")
        if st.session_state.chatbot:
            saved_exclusions = st.session_state.chatbot.saved_exclusions
            if saved_exclusions:
                st.success(f"Allergies: {', '.join(saved_exclusions)}")
            else:
                st.caption("_No saved allergies_")

        st.markdown("---")

        # Clear conversation
        if st.button("🔄 Clear Conversation"):
            st.session_state.messages = [st.session_state.messages[0]]  # Keep welcome message
            st.session_state.chatbot = PetProductChatbot()
            st.session_state.last_response = None
            st.rerun()

        st.markdown("---")

        # Info Section
        st.subheader("ℹ️ About")
        st.markdown("""
        This chatbot demonstrates:
        - **Vector Search** with embeddings
        - **Negative Intent** handling ("salmon-free")
        - **LLM-based NLU** (GPT function calling)
        - **Multi-turn** conversation
        - **Customer memory** across sessions

        Built with:
        - OpenAI (embeddings + NLU)
        - Chroma (vector database)
        - LangChain
        - Streamlit
        """)

        st.caption("_Interview demo project_")

# ==================== Product Display ====================

def render_product_card(product: Dict, rank: int):
    """Render a single product card."""
    with st.container():
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(f"**{rank}. {product['name']}**")
            st.caption(f"🏷️ {product.get('brand', 'Unknown')} | 🐾 {product.get('target_pet', 'Unknown')}")

        with col2:
            st.markdown(f"<div class='product-price'>${product.get('price', 0):.2f}</div>", unsafe_allow_html=True)
            if st.session_state.debug_mode:
                st.caption(f"Similarity: {product.get('similarity', 0):.3f}")

        # Show ingredients if available
        if 'ingredients' in product and product['ingredients']:
            ingredients = product['ingredients']
            if isinstance(ingredients, str):
                ingredients = ingredients.split(',')[:5]  # Show first 5
            st.caption(f"🥘 {', '.join(ingredients)}")

        st.markdown("---")

# ==================== Debug Panel ====================

def render_debug_panel(response: Dict):
    """Render debug information."""
    if not st.session_state.debug_mode or not response:
        return

    with st.expander("🔍 Debug Information", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Intent & Entities")
            intent = response.get('intent', {})
            st.json(intent)

        with col2:
            st.subheader("Conversation Context")
            context = response.get('context', 'N/A')
            st.text(context)

        # Show all results with similarity scores
        st.subheader("Retrieved Products (All)")
        results = response.get('results', [])
        if results:
            for i, product in enumerate(results, 1):
                st.text(f"{i}. {product['name'][:50]}... | ${product['price']:.2f} | Sim: {product['similarity']:.3f}")

# ==================== Main Chat Interface ====================

def main():
    """Main application."""
    initialize_session_state()
    render_sidebar()

    # Header
    st.title("🐾 Pet Product Chatbot")
    st.caption("Ask me about pet products using natural language!")

    # Chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            # Show products if this is a bot message with results
            if message["role"] == "assistant" and "products" in message:
                st.markdown("### 🛍️ Recommended Products")
                for i, product in enumerate(message["products"], 1):
                    render_product_card(product, i)

    # Chat input
    if prompt := st.chat_input("Ask about pet products..."):
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get bot response
        with st.chat_message("assistant"):
            with st.spinner("🔍 Searching..."):
                response = st.session_state.chatbot.chat(prompt)
                st.session_state.last_response = response

                results = response.get('results', [])

                if results:
                    # Create response message
                    result_count = len(results)
                    response_text = f"Found **{result_count} products** for you!"
                    st.markdown(response_text)

                    # Show products
                    st.markdown("### 🛍️ Recommended Products")
                    for i, product in enumerate(results[:5], 1):  # Show top 5
                        render_product_card(product, i)

                    # Add to message history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response_text,
                        "products": results[:5]
                    })
                else:
                    no_results_msg = "Sorry, I couldn't find any products matching your criteria. Try adjusting your filters!"
                    st.markdown(no_results_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": no_results_msg
                    })

        # Show debug panel if enabled
        render_debug_panel(st.session_state.last_response)

        # Rerun to update sidebar context
        st.rerun()

if __name__ == "__main__":
    main()
